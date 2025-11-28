import csv

from django.db import transaction
from django.utils import timezone

from products.choices import ImportJobStatuses, WebhookEventTypes
from products.constants import ImportJobConstants, ProductConstants
from products.dbio import ImportJobDbIO, ProductDbIO
from products.tasks import trigger_webhooks_for_event


class CsvProcessor:
    
    def __init__(self, import_job_uuid):
        self.import_job_uuid = import_job_uuid
        self.import_job_dbio = ImportJobDbIO()
        self.product_dbio = ProductDbIO()
        self.import_job = None
    
    def process_csv_file(self, file_path):
        self.import_job = self.import_job_dbio.get_obj({
            'uuid': self.import_job_uuid
            })
        
        self._update_job_status(ImportJobStatuses.PROCESSING)
        self.import_job.started_at = timezone.now()
        self.import_job.save(update_fields=['status', 'started_at'])
        
        try:
            total_records = self._count_csv_rows(file_path)
            self.import_job.total_records = total_records
            self.import_job.save(update_fields=['total_records'])
            
            self._process_csv_in_chunks(file_path)
            
            self._update_job_status(ImportJobStatuses.COMPLETED)
            self.import_job.completed_at = timezone.now()
            self.import_job.save(update_fields=['status', 'completed_at'])
            
            self._trigger_import_completed_webhook()
            
        except Exception as e:
            self._handle_processing_error(str(e))
            self._trigger_import_failed_webhook(str(e))
            raise
    
    def _count_csv_rows(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return sum(1 for _ in reader)
    
    def _process_csv_in_chunks(self, file_path):
        chunk_size = ProductConstants.CSV_CHUNK_SIZE
        chunk = []
        processed_count = 0
        progress_update_interval = ProductConstants.PROGRESS_UPDATE_INTERVAL
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                processed_row = self._process_row(row)
                if processed_row:
                    chunk.append(processed_row)
                
                if len(chunk) >= chunk_size:
                    self._bulk_upsert_products(chunk)
                    processed_count += len(chunk)
                    
                    if processed_count % progress_update_interval == 0:
                        self._update_progress(processed_count)
                    
                    chunk = []
            
            if chunk:
                self._bulk_upsert_products(chunk)
                processed_count += len(chunk)
            
            self._update_progress(processed_count)
    
    def _process_row(self, row):
        try:
            sku = row.get('sku', '').strip()
            name = row.get('name', '').strip()
            description = row.get('description', '').strip() or None
            
            if not sku or not name:
                self.import_job.failed_records += 1
                return None
            
            if len(sku) > ProductConstants.SKU_MAX_LENGTH:
                self.import_job.failed_records += 1
                return None
            
            if len(name) > ProductConstants.PRODUCT_NAME_MAX_LENGTH:
                self.import_job.failed_records += 1
                return None
            
            if description and len(description) > ProductConstants.DESCRIPTION_MAX_LENGTH:
                description = description[:ProductConstants.DESCRIPTION_MAX_LENGTH]
            
            return {
                'sku': sku.lower(),
                'name': name,
                'description': description,
            }
        except Exception:
            self.import_job.failed_records += 1
            return None
    
    @transaction.atomic
    def _bulk_upsert_products(self, products_data):
        if not products_data:
            return
        
        existing_skus = set()
        existing_products = {}
        
        skus = [p['sku'] for p in products_data]
        existing_products_qs = self.product_dbio.filter_obj({'sku__in': skus}).only('sku', 'name', 'description')
        
        for product in existing_products_qs:
            existing_skus.add(product.sku)
            existing_products[product.sku] = product
        
        products_to_create = []
        products_to_update = []
        current_time = timezone.now()
        
        for product_data in products_data:
            sku = product_data['sku']
            if sku in existing_skus:
                existing_product = existing_products[sku]
                existing_product.name = product_data['name']
                existing_product.description = product_data['description']
                existing_product.updated_at = current_time
                products_to_update.append(existing_product)
            else:
                product = self.product_dbio.model(**product_data)
                product.created_at = current_time
                product.updated_at = current_time
                products_to_create.append(product)
        
        if products_to_create:
            batch_size = ProductConstants.BULK_CREATE_BATCH_SIZE
            for i in range(0, len(products_to_create), batch_size):
                batch = products_to_create[i:i + batch_size]
                self.product_dbio.model.objects.bulk_create(
                    batch,
                    ignore_conflicts=False
                )
            self.import_job.successful_records += len(products_to_create)
        
        if products_to_update:
            batch_size = ProductConstants.BULK_UPDATE_BATCH_SIZE
            for i in range(0, len(products_to_update), batch_size):
                batch = products_to_update[i:i + batch_size]
                self.product_dbio.model.objects.bulk_update(
                    batch,
                    ['name', 'description', 'updated_at']
                )
            self.import_job.successful_records += len(products_to_update)
        
        self.import_job.processed_records += len(products_data)
        self.import_job.save(
            update_fields=['successful_records', 'processed_records']
        )
    
    def _update_progress(self, processed_count):
        if self.import_job.total_records > 0:
            progress = int(
                (processed_count / self.import_job.total_records) * 
                ImportJobConstants.PROGRESS_MAX
            )
            self.import_job.progress = min(progress, ImportJobConstants.PROGRESS_MAX)
            self.import_job.save(update_fields=['progress'])
    
    def _update_job_status(self, status):
        self.import_job.status = status
        self.import_job.save(update_fields=['status'])
    
    def _handle_processing_error(self, error_message):
        self.import_job.status = ImportJobStatuses.FAILED
        self.import_job.error_message = error_message
        self.import_job.completed_at = timezone.now()
        self.import_job.save(
            update_fields=['status', 'error_message', 'completed_at']
        )
    
    def _trigger_import_completed_webhook(self):
        from products.handlers.import_job_handler import ImportJobHandler
        
        job_data = ImportJobHandler().get_job_status(str(self.import_job.uuid))
        trigger_webhooks_for_event.delay(
            WebhookEventTypes.IMPORT_COMPLETED,
            {'import_job': job_data}
        )
    
    def _trigger_import_failed_webhook(self, error_message):
        from products.handlers.import_job_handler import ImportJobHandler
        
        job_data = ImportJobHandler().get_job_status(str(self.import_job.uuid))
        job_data['error_message'] = error_message
        trigger_webhooks_for_event.delay(
            WebhookEventTypes.IMPORT_FAILED,
            {'import_job': job_data}
        )

