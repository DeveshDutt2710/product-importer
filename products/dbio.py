from base.dbio import BaseDbIO
from products.models import (
    ImportJob,
    Product,
    Webhook
)


class ProductDbIO(BaseDbIO):
    
    @property
    def model(self):
        return Product


class WebhookDbIO(BaseDbIO):
    
    @property
    def model(self):
        return Webhook


class ImportJobDbIO(BaseDbIO):
    
    @property
    def model(self):
        return ImportJob

