class WebhookEventTypes:
    PRODUCT_CREATED = 'product.created'
    PRODUCT_UPDATED = 'product.updated'
    PRODUCT_DELETED = 'product.deleted'
    IMPORT_COMPLETED = 'import.completed'
    IMPORT_FAILED = 'import.failed'


WEBHOOK_EVENT_TYPES = (
    (WebhookEventTypes.PRODUCT_CREATED, 'Product Created'),
    (WebhookEventTypes.PRODUCT_UPDATED, 'Product Updated'),
    (WebhookEventTypes.PRODUCT_DELETED, 'Product Deleted'),
    (WebhookEventTypes.IMPORT_COMPLETED, 'Import Completed'),
    (WebhookEventTypes.IMPORT_FAILED, 'Import Failed'),
)


class ImportJobStatuses:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


IMPORT_JOB_STATUS_CHOICES = (
    (ImportJobStatuses.PENDING, 'Pending'),
    (ImportJobStatuses.PROCESSING, 'Processing'),
    (ImportJobStatuses.COMPLETED, 'Completed'),
    (ImportJobStatuses.FAILED, 'Failed'),
)
