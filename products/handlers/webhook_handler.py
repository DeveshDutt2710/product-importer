import json
import time

import requests

from base.choices import StateStatuses
from products.choices import WebhookEventTypes
from products.constants import WebhookConstants
from products.dbio import WebhookDbIO
from products.models import Webhook


class WebhookHandler:
    
    def __init__(self):
        self.webhook_dbio = WebhookDbIO()
    
    def validate_webhook_data(self, data):
        errors = {}
        
        url = data.get('url', '').strip()
        if not url:
            errors['url'] = 'URL is required'
        elif len(url) > WebhookConstants.WEBHOOK_URL_MAX_LENGTH:
            errors['url'] = f'URL must be at most {WebhookConstants.WEBHOOK_URL_MAX_LENGTH} characters'
        
        event_type = data.get('event_type', '').strip()
        if not event_type:
            errors['event_type'] = 'Event type is required'
        elif len(event_type) > WebhookConstants.EVENT_TYPE_MAX_LENGTH:
            errors['event_type'] = f'Event type must be at most {WebhookConstants.EVENT_TYPE_MAX_LENGTH} characters'
        
        secret = data.get('secret', '').strip() if data.get('secret') else None
        if secret and len(secret) > WebhookConstants.SECRET_MAX_LENGTH:
            errors['secret'] = f'Secret must be at most {WebhookConstants.SECRET_MAX_LENGTH} characters'
        
        enabled = data.get('enabled')
        if enabled is not None:
            if not isinstance(enabled, bool):
                enabled = str(enabled).lower() in ('true', '1', 'yes')
        
        if errors:
            raise ValueError(errors)
        
        result = {
            'url': url,
            'event_type': event_type,
            'secret': secret,
        }
        
        if enabled is not None:
            result['enabled'] = enabled
        
        return result
    
    def webhook_to_dict(self, webhook):
        return {
            'uuid': str(webhook.uuid),
            'url': webhook.url,
            'event_type': webhook.event_type,
            'enabled': webhook.enabled,
            'created_at': webhook.created_at.isoformat() if webhook.created_at else None,
            'updated_at': webhook.updated_at.isoformat() if webhook.updated_at else None,
        }
    
    def create_webhook(self, data):
        validated_data = self.validate_webhook_data(data)
        enabled = validated_data.pop('enabled', True)
        webhook = self.webhook_dbio.create_obj(validated_data)
        if not enabled:
            webhook.enabled = False
            webhook.save()
        return self.webhook_to_dict(webhook)
    
    def get_webhook(self, webhook_uuid):
        webhook = self.webhook_dbio.get_obj({'uuid': webhook_uuid})
        return self.webhook_to_dict(webhook)
    
    def update_webhook(self, webhook_uuid, data):
        validated_data = self.validate_webhook_data(data)
        enabled = validated_data.pop('enabled', None)
        webhook = self.webhook_dbio.get_obj({'uuid': webhook_uuid})
        self.webhook_dbio.update_obj(webhook, validated_data)
        if enabled is not None:
            webhook.enabled = enabled
            webhook.save()
        return self.webhook_to_dict(webhook)
    
    def delete_webhook(self, webhook_uuid):
        webhook = self.webhook_dbio.get_obj({'uuid': webhook_uuid})
        webhook.soft_delete()
        return {'message': 'Webhook deleted successfully'}
    
    def list_webhooks(self, filters=None):
        if filters is None:
            filters = {}
        
        queryset = self.webhook_dbio.get_all_active()
        
        event_type = filters.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        enabled = filters.get('enabled')
        if enabled is not None:
            if enabled:
                queryset = queryset.filter(state=StateStatuses.ACTIVE)
            else:
                queryset = queryset.filter(state=StateStatuses.INACTIVE)
        
        webhooks_list = [self.webhook_to_dict(webhook) for webhook in queryset]
        
        return {
            'results': webhooks_list,
            'total_count': len(webhooks_list),
        }
    
    def get_webhooks_for_event(self, event_type):
        webhooks = self.webhook_dbio.filter_active_obj({
            'event_type': event_type
        })
        return list(webhooks)
    
    def deliver_webhook(self, webhook, payload):
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ProductImporter/1.0'
            }
            
            if webhook.secret:
                headers['X-Webhook-Secret'] = webhook.secret
            
            start_time = time.time()
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=WebhookConstants.WEBHOOK_TIMEOUT
            )
            response_time = time.time() - start_time
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'response_body': response.text[:500] if response.text else None,
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status_code': None,
                'response_time': None,
                'error': 'Request timeout',
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'status_code': None,
                'response_time': None,
                'error': str(e),
            }
    
    def test_webhook(self, webhook_uuid):
        webhook = self.webhook_dbio.get_obj({'uuid': webhook_uuid})
        
        test_payload = {
            'event_type': webhook.event_type,
            'test': True,
            'timestamp': time.time(),
            'message': 'This is a test webhook',
        }
        
        return self.deliver_webhook(webhook, test_payload)

