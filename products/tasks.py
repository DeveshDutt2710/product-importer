from celery import shared_task

from products.handlers.csv_processor import CsvProcessor
from products.handlers.webhook_handler import WebhookHandler
from products.choices import WebhookEventTypes


@shared_task
def process_csv_import(import_job_uuid, file_path):
    processor = CsvProcessor(import_job_uuid)
    processor.process_csv_file(file_path)


@shared_task
def deliver_webhook_task(webhook_uuid, event_type, payload):
    from products.dbio import WebhookDbIO
    
    webhook_dbio = WebhookDbIO()
    try:
        webhook = webhook_dbio.get_obj({'uuid': webhook_uuid})
    except webhook_dbio.model.DoesNotExist:
        return {'success': False, 'error': 'Webhook not found'}
    
    handler = WebhookHandler()
    result = handler.deliver_webhook(webhook, payload)
    
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

