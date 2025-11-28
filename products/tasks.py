from celery import shared_task

from products.handlers.csv_processor import CsvProcessor


@shared_task
def process_csv_import(import_job_uuid, file_path):
    processor = CsvProcessor(import_job_uuid)
    processor.process_csv_file(file_path)

