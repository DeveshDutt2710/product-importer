from django.contrib import admin

from base.admin import BaseAdmin
from products.models import (
    ImportJob,
    Product,
    Webhook
)


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ('sku', 'name', 'created_at', 'state')
    search_fields = ('sku', 'name')
    list_filter = ('state', 'created_at')


@admin.register(Webhook)
class WebhookAdmin(BaseAdmin):
    list_display = ('url', 'event_type', 'state', 'created_at')
    search_fields = ('url', 'event_type')
    list_filter = ('event_type', 'state', 'created_at')


@admin.register(ImportJob)
class ImportJobAdmin(BaseAdmin):
    list_display = ('uuid', 'status', 'progress', 'total_records', 'created_at')
    search_fields = ('file_name', 'status')
    list_filter = ('status', 'state', 'created_at')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'started_at', 'completed_at')

