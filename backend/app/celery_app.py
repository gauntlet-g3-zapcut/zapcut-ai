import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery only if REDIS_URL is configured
# This allows the app to start even if Redis is not available
celery_app = None

if settings.REDIS_URL:
    try:
        celery_app = Celery(
            "zapcut",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
            include=["app.tasks.video_generation"]
        )

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
        logger.info("Celery configured with Redis successfully")
    except Exception as e:
        logger.error(f"Celery initialization failed: {e}", exc_info=True)
        celery_app = None
else:
    logger.warning("REDIS_URL not configured - Celery tasks will not be available")

