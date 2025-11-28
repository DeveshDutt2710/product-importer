from django.urls import path

from products.views import CsvUploadView, ImportJobStatusView, upload_page

urlpatterns = [
    path('', upload_page, name='upload-page'),
    path('api/upload/', CsvUploadView.as_view(), name='csv-upload'),
    path('api/import/<uuid:job_id>/status/', ImportJobStatusView.as_view(), name='import-job-status'),
]
