from django.shortcuts import render
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser

from base.response import APIResponse
from base.views import AbstractAPIView
from products.handlers.csv_upload_handler import CsvUploadHandler
from products.handlers.import_job_handler import ImportJobHandler


def upload_page(request):
    return render(request, 'products/upload.html')


class CsvUploadView(AbstractAPIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return APIResponse(
                data={'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        try:
            data = CsvUploadHandler().upload_csv_file(uploaded_file)
            return APIResponse(data=data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return APIResponse(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to process upload: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImportJobStatusView(AbstractAPIView):
    
    def get(self, request, *args, **kwargs):
        job_uuid = kwargs.get('job_id')
        
        try:
            data = ImportJobHandler().get_job_status(job_uuid)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except ValueError as e:
            return APIResponse(
                data={'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to get job status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
