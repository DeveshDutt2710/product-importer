from django.core.paginator import Paginator

from base.choices import StateStatuses
from base.constants import BaseConstants
from products.constants import ProductConstants
from products.dbio import ProductDbIO
from products.models import Product


class ProductHandler:
    
    def __init__(self):
        self.product_dbio = ProductDbIO()
    
    def validate_product_data(self, data):
        errors = {}
        
        sku = data.get('sku', '').strip()
        if not sku:
            errors['sku'] = 'SKU is required'
        elif len(sku) > ProductConstants.SKU_MAX_LENGTH:
            errors['sku'] = f'SKU must be at most {ProductConstants.SKU_MAX_LENGTH} characters'
        
        name = data.get('name', '').strip()
        if not name:
            errors['name'] = 'Name is required'
        elif len(name) > ProductConstants.PRODUCT_NAME_MAX_LENGTH:
            errors['name'] = f'Name must be at most {ProductConstants.PRODUCT_NAME_MAX_LENGTH} characters'
        
        description = data.get('description', '').strip() if data.get('description') else None
        if description and len(description) > ProductConstants.DESCRIPTION_MAX_LENGTH:
            errors['description'] = f'Description must be at most {ProductConstants.DESCRIPTION_MAX_LENGTH} characters'
        
        if errors:
            raise ValueError(errors)
        
        return {
            'sku': sku.lower(),
            'name': name,
            'description': description,
        }
    
    def product_to_dict(self, product):
        return {
            'uuid': str(product.uuid),
            'sku': product.sku,
            'name': product.name,
            'description': product.description,
            'active': product.active,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None,
        }
    
    def create_product(self, data):
        validated_data = self.validate_product_data(data)
        product = self.product_dbio.create_obj(validated_data)
        return self.product_to_dict(product)
    
    def get_product(self, product_uuid):
        product = self.product_dbio.get_obj({'uuid': product_uuid})
        return self.product_to_dict(product)
    
    def update_product(self, product_uuid, data):
        validated_data = self.validate_product_data(data)
        product = self.product_dbio.get_obj({'uuid': product_uuid})
        self.product_dbio.update_obj(product, validated_data)
        return self.product_to_dict(product)
    
    def delete_product(self, product_uuid):
        product = self.product_dbio.get_obj({'uuid': product_uuid})
        product.soft_delete()
        return {'message': 'Product deleted successfully'}
    
    def list_products(self, filters=None, page=None, page_size=None):
        if filters is None:
            filters = {}
        
        queryset = self.product_dbio.get_all_active().only(
            'uuid', 'sku', 'name', 'description', 'state', 'created_at', 'updated_at'
        )
        
        sku = filters.get('sku')
        if sku:
            queryset = queryset.filter(sku__icontains=sku.lower())
        
        name = filters.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        description = filters.get('description')
        if description:
            queryset = queryset.filter(description__icontains=description)
        
        active = filters.get('active')
        if active is not None:
            if active:
                queryset = queryset.filter(state=StateStatuses.ACTIVE)
            else:
                queryset = queryset.filter(state=StateStatuses.INACTIVE)
        
        page_size = page_size or BaseConstants.PAGINATION_PAGE_SIZE
        page = page or 1
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        products_list = [self.product_to_dict(product) for product in page_obj]
        
        return {
            'results': products_list,
            'total_count': paginator.count,
            'page': page_obj.number,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    def bulk_delete_all_products(self):
        products = self.product_dbio.get_all()
        count = products.count()
        
        if count > 0:
            from base.choices import StateStatuses
            products.update(state=StateStatuses.INACTIVE)
        
        return count

