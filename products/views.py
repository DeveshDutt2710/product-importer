from django.shortcuts import render
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser

from base.constants import BaseConstants
from base.response import APIResponse
from base.views import AbstractAPIView
from products.handlers.csv_upload_handler import CsvUploadHandler
from products.handlers.import_job_handler import ImportJobHandler
from products.handlers.product_handler import ProductHandler
from products.handlers.webhook_handler import WebhookHandler
from products.models import Product, Webhook
from products.tasks import trigger_webhooks_for_event


def upload_page(request):
    return render(request, 'products/upload.html')


def products_page(request):
    return render(request, 'products/products.html')


def webhooks_page(request):
    return render(request, 'products/webhooks.html')


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


class ProductListView(AbstractAPIView):
    
    def get(self, request, *args, **kwargs):
        filters = {}
        
        sku = request.GET.get('sku')
        if sku:
            filters['sku'] = sku
        
        name = request.GET.get('name')
        if name:
            filters['name'] = name
        
        description = request.GET.get('description')
        if description:
            filters['description'] = description
        
        active_param = request.GET.get('active')
        if active_param is not None:
            filters['active'] = self.get_bool_query_value('active')
        
        page = request.GET.get('page')
        page = int(page) if page and page.isdigit() else 1
        
        page_size = request.GET.get('page_size')
        page_size = int(page_size) if page_size and page_size.isdigit() else BaseConstants.PAGINATION_PAGE_SIZE
        
        try:
            data = ProductHandler().list_products(filters, page, page_size)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to list products: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, *args, **kwargs):
        try:
            data = ProductHandler().create_product(request.data)
            from products.choices import WebhookEventTypes
            trigger_webhooks_for_event.delay(
                WebhookEventTypes.PRODUCT_CREATED,
                {'product': data}
            )
            return APIResponse(data=data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return APIResponse(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to create product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductDetailView(AbstractAPIView):
    
    def get(self, request, *args, **kwargs):
        product_uuid = kwargs.get('product_id')
        
        try:
            data = ProductHandler().get_product(product_uuid)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return APIResponse(
                data={'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to get product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, *args, **kwargs):
        product_uuid = kwargs.get('product_id')
        
        try:
            data = ProductHandler().update_product(product_uuid, request.data)
            from products.choices import WebhookEventTypes
            trigger_webhooks_for_event.delay(
                WebhookEventTypes.PRODUCT_UPDATED,
                {'product': data}
            )
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return APIResponse(
                data={'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return APIResponse(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to update product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, *args, **kwargs):
        product_uuid = kwargs.get('product_id')
        
        try:
            product_data = ProductHandler().get_product(product_uuid)
            data = ProductHandler().delete_product(product_uuid)
            from products.choices import WebhookEventTypes
            trigger_webhooks_for_event.delay(
                WebhookEventTypes.PRODUCT_DELETED,
                {'product': product_data}
            )
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return APIResponse(
                data={'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to delete product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductBulkDeleteView(AbstractAPIView):
    
    def post(self, request, *args, **kwargs):
        try:
            count = ProductHandler().bulk_delete_all_products()
            return APIResponse(
                data={'message': f'Successfully deleted {count} products'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to delete products: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookListView(AbstractAPIView):
    
    def get(self, request, *args, **kwargs):
        filters = {}
        
        event_type = request.GET.get('event_type')
        if event_type:
            filters['event_type'] = event_type
        
        enabled_param = request.GET.get('enabled')
        if enabled_param is not None:
            filters['enabled'] = self.get_bool_query_value('enabled')
        
        try:
            data = WebhookHandler().list_webhooks(filters)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to list webhooks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, *args, **kwargs):
        try:
            data = WebhookHandler().create_webhook(request.data)
            return APIResponse(data=data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return APIResponse(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to create webhook: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookDetailView(AbstractAPIView):
    
    def get(self, request, *args, **kwargs):
        webhook_uuid = kwargs.get('webhook_id')
        
        try:
            data = WebhookHandler().get_webhook(webhook_uuid)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Webhook.DoesNotExist:
            return APIResponse(
                data={'error': 'Webhook not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to get webhook: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, *args, **kwargs):
        webhook_uuid = kwargs.get('webhook_id')
        
        try:
            data = WebhookHandler().update_webhook(webhook_uuid, request.data)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Webhook.DoesNotExist:
            return APIResponse(
                data={'error': 'Webhook not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return APIResponse(
                data={'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to update webhook: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, *args, **kwargs):
        webhook_uuid = kwargs.get('webhook_id')
        
        try:
            data = WebhookHandler().delete_webhook(webhook_uuid)
            return APIResponse(data=data, status=status.HTTP_200_OK)
        except Webhook.DoesNotExist:
            return APIResponse(
                data={'error': 'Webhook not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to delete webhook: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookTestView(AbstractAPIView):
    
    def post(self, request, *args, **kwargs):
        webhook_uuid = kwargs.get('webhook_id')
        
        try:
            result = WebhookHandler().test_webhook(webhook_uuid)
            return APIResponse(data=result, status=status.HTTP_200_OK)
        except Webhook.DoesNotExist:
            return APIResponse(
                data={'error': 'Webhook not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return APIResponse(
                data={'error': f'Failed to test webhook: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
