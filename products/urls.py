from django.urls import path

from products.views import (
    CsvUploadView,
    ImportJobStatusView,
    ProductBulkDeleteView,
    ProductDetailView,
    ProductListView,
    upload_page
)

urlpatterns = [
    path('', upload_page, name='upload-page'),
    path('api/upload/', CsvUploadView.as_view(), name='csv-upload'),
    path('api/import/<uuid:job_id>/status/', ImportJobStatusView.as_view(), name='import-job-status'),
    path('api/products/', ProductListView.as_view(), name='product-list'),
    path('api/products/<uuid:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('api/products/bulk-delete/', ProductBulkDeleteView.as_view(), name='product-bulk-delete'),
]
