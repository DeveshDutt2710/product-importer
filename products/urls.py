from django.urls import path

from products.views import CsvUploadView

urlpatterns = [
    path('api/upload/', CsvUploadView.as_view(), name='csv-upload'),
]
