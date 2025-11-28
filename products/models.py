from django.db import models

from base.choices import StateStatuses
from base.models import AbstractBaseModel
from products.choices import (
    IMPORT_JOB_STATUS_CHOICES,
    ImportJobStatuses,
    WEBHOOK_EVENT_TYPES
)
from products.constants import (
    ImportJobConstants,
    ProductConstants,
    WebhookConstants
)


class Product(AbstractBaseModel):
    
    sku = models.CharField(
        max_length=ProductConstants.SKU_MAX_LENGTH,
        unique=True,
        db_index=True
    )
    name = models.CharField(
        max_length=ProductConstants.PRODUCT_NAME_MAX_LENGTH)
    description = models.TextField(
        blank=True,
        null=True,
        max_length=ProductConstants.DESCRIPTION_MAX_LENGTH
    )
    
    def save(self, *args, **kwargs):
        self.sku = self.sku.lower().strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    @property
    def active(self):
        return self.state == StateStatuses.ACTIVE
    
    @active.setter
    def active(self, value):
        self.state = StateStatuses.ACTIVE if value else StateStatuses.INACTIVE
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['state']),
            models.Index(fields=['name']),
        ]


class Webhook(AbstractBaseModel):
    
    url = models.URLField(
        max_length=WebhookConstants.WEBHOOK_URL_MAX_LENGTH)
    event_type = models.CharField(
        max_length=WebhookConstants.EVENT_TYPE_MAX_LENGTH,
        choices=WEBHOOK_EVENT_TYPES
    )
    secret = models.CharField(
        max_length=WebhookConstants.SECRET_MAX_LENGTH,
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"{self.event_type} -> {self.url}"
    
    @property
    def enabled(self):
        return self.state == StateStatuses.ACTIVE
    
    @enabled.setter
    def enabled(self, value):
        self.state = StateStatuses.ACTIVE if value else StateStatuses.INACTIVE
    
    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']
        unique_together = [['url', 'event_type']]
        indexes = [
            models.Index(fields=['state', 'event_type']),
        ]


class ImportJob(AbstractBaseModel):
    
    status = models.CharField(
        max_length=ImportJobConstants.STATUS_MAX_LENGTH,
        choices=IMPORT_JOB_STATUS_CHOICES,
        default=ImportJobStatuses.PENDING,
        db_index=True
    )
    progress = models.IntegerField(default=0)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    file_name = models.CharField(
        max_length=ImportJobConstants.FILE_NAME_MAX_LENGTH,
        blank=True
    )
    file_size = models.BigIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"ImportJob {self.uuid} - {self.status} ({self.progress}%)"
    
    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    class Meta:
        db_table = 'import_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['state']),
        ]
