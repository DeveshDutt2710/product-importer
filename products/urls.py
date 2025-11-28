from django.urls import path

from products.views import (
    CsvUploadView,
    ImportJobStatusView,
    ProductBulkDeleteView,
    ProductDetailView,
    ProductListView,
    WebhookDetailView,
    WebhookListView,
    WebhookTestView,
    products_page,
    upload_page,
    webhooks_page
)

urlpatterns = [
    path('', upload_page, name='upload-page'),
    path('products/', products_page, name='products-page'),
    path('webhooks/', webhooks_page, name='webhooks-page'),
    path('api/upload/', CsvUploadView.as_view(), name='csv-upload'),
    path('api/import/<uuid:job_id>/status/', ImportJobStatusView.as_view(), name='import-job-status'),
    path('api/products/', ProductListView.as_view(), name='product-list'),
    path('api/products/<uuid:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('api/products/bulk-delete/', ProductBulkDeleteView.as_view(), name='product-bulk-delete'),
    path('api/webhooks/', WebhookListView.as_view(), name='webhook-list'),
    path('api/webhooks/<uuid:webhook_id>/', WebhookDetailView.as_view(), name='webhook-detail'),
    path('api/webhooks/<uuid:webhook_id>/test/', WebhookTestView.as_view(), name='webhook-test'),
]
