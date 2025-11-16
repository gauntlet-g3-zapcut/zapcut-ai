import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,  # 2 hours max (hard limit)
    task_soft_time_limit=6600,  # 110 minutes soft limit (gives 10 min warning before hard limit)
)

