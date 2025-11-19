"""Celery application configuration."""
import logging
import ssl
import sys
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
# Upstash Redis requires SSL, so we need to configure broker_connection_retry_on_startup
redis_url = settings.REDIS_URL or 'redis://localhost:6379/0'

# If using rediss:// (SSL), add ssl_cert_reqs parameter to URL
if redis_url.startswith('rediss://'):
    # Add ssl_cert_reqs=none to the URL for Upstash Redis
    if '?' in redis_url:
        broker_url = f"{redis_url}&ssl_cert_reqs=none"
        backend_url = f"{redis_url}&ssl_cert_reqs=none"
    else:
        broker_url = f"{redis_url}?ssl_cert_reqs=none"
        backend_url = f"{redis_url}?ssl_cert_reqs=none"
else:
    broker_url = redis_url
    backend_url = redis_url

celery_app = Celery(
    'zapcut',
    broker=broker_url,
    backend=backend_url,
    include=['app.tasks.video_generation', 'app.tasks.audio_generation']
)

# Celery configuration
celery_config = {
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 600,  # 10 minutes per task
    'task_soft_time_limit': 540,  # 9 minutes soft limit
    'worker_prefetch_multiplier': 1,  # Prevent task hoarding
    'worker_max_tasks_per_child': 50,  # Restart workers after 50 tasks
    'task_acks_late': True,  # Acknowledge tasks after completion
    'task_reject_on_worker_lost': True,  # Reject tasks if worker dies
    'broker_connection_retry_on_startup': True,  # Retry connection on startup
    # SSL configuration for Upstash Redis
    'broker_connection_ssl': {'ssl_cert_reqs': ssl.CERT_NONE},
    'result_backend_transport_options': {
        'ssl_cert_reqs': ssl.CERT_NONE,
    },
}

# Use threads pool on macOS to avoid fork safety issues while maintaining concurrency
# prefork pool works fine on Linux (production)
if sys.platform == 'darwin':  # macOS
    celery_config['worker_pool'] = 'threads'
    celery_config['worker_concurrency'] = 10  # Allow up to 10 concurrent tasks
    logger.info("Using 'threads' worker pool with concurrency=10 for macOS compatibility")
else:
    logger.info("Using default 'prefork' worker pool for Linux")

celery_app.conf.update(celery_config)

logger.info("Celery app initialized")
