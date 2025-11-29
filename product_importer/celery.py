import os
import ssl

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_importer.settings')

def add_ssl_to_redis_url(url):
    if url and url.startswith('rediss://') and 'ssl_cert_reqs' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}ssl_cert_reqs=CERT_NONE"
    return url

broker_url_env = os.environ.get('CELERY_BROKER_URL') or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
result_backend_env = os.environ.get('CELERY_RESULT_BACKEND') or broker_url_env

broker_url_env = add_ssl_to_redis_url(broker_url_env)
result_backend_env = add_ssl_to_redis_url(result_backend_env)

os.environ['CELERY_BROKER_URL'] = broker_url_env
os.environ['CELERY_RESULT_BACKEND'] = result_backend_env
if 'REDIS_URL' in os.environ:
    os.environ['REDIS_URL'] = add_ssl_to_redis_url(os.environ['REDIS_URL'])

app = Celery('product_importer')

app.conf.broker_url = broker_url_env
app.conf.result_backend = result_backend_env

app.config_from_object('django.conf:settings', namespace='CELERY')

broker_url = app.conf.broker_url
result_backend = app.conf.result_backend

broker_url = add_ssl_to_redis_url(broker_url)
result_backend = add_ssl_to_redis_url(result_backend)

app.conf.broker_url = broker_url
app.conf.result_backend = result_backend

ssl_options = {
    'ssl_cert_reqs': ssl.CERT_NONE,
    'ssl_ca_certs': None,
    'ssl_certfile': None,
    'ssl_keyfile': None,
}

if broker_url and broker_url.startswith('rediss://'):
    app.conf.broker_use_ssl = ssl_options
    app.conf.broker_transport_options = ssl_options

if result_backend and result_backend.startswith('rediss://'):
    app.conf.result_backend_transport_options = ssl_options

app.autodiscover_tasks()

