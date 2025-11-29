from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from products.handlers.csv_processor import CsvProcessor
from products.handlers.webhook_handler import WebhookHandler
from products.choices import WebhookEventTypes


@shared_task(
    time_limit=60 * 60,
    soft_time_limit=55 * 60
)
def process_csv_import(import_job_uuid, file_path):
    processor = CsvProcessor(import_job_uuid)
    try:
        processor.process_csv_file(file_path)
    except SoftTimeLimitExceeded:
        error_msg = (
            'Import task exceeded time limit (55 minutes). '
            'The file may be too large or processing is too slow on the current CPU tier. '
            'Please try with a smaller file or consider upgrading to a higher CPU tier.'
        )
        if processor.import_job is None:
            processor.import_job = processor.import_job_dbio.get_obj({'uuid': import_job_uuid})
        processor._handle_processing_error(error_msg)
        processor._trigger_import_failed_webhook(error_msg)
        raise


@shared_task
def deliver_webhook_task(webhook_uuid, event_type, payload):
    from products.dbio import WebhookDbIO
    
    webhook_dbio = WebhookDbIO()
    try:
        webhook = webhook_dbio.get_obj({'uuid': webhook_uuid})
    except webhook_dbio.model.DoesNotExist:
        return {'success': False, 'error': 'Webhook not found'}
    
    handler = WebhookHandler()
    result = handler.deliver_webhook(webhook, event_type, payload)
    
    if not result['success']:
        retry_count = payload.get('_retry_count', 0)
        if retry_count < 3:
            deliver_webhook_task.apply_async(
                args=[webhook_uuid, event_type, {**payload, '_retry_count': retry_count + 1}],
                countdown=5 * (retry_count + 1)
            )
    
    return result


@shared_task
def trigger_webhooks_for_event(event_type, payload):
    handler = WebhookHandler()
    webhooks = handler.get_webhooks_for_event(event_type)
    
    for webhook in webhooks:
        deliver_webhook_task.delay(str(webhook.uuid), event_type, payload)

