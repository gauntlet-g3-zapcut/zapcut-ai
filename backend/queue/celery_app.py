from celery import Celery
from app.config import settings

# Initialize Celery only if REDIS_URL is configured
# This allows the app to start even if Redis is not available
celery_app = None

if settings.REDIS_URL:
    try:
        celery_app = Celery(
            "adcraft",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
            include=["queue.tasks.video_generation"]
        )
        
        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            task_time_limit=3600,  # 1 hour max
            task_soft_time_limit=3000,  # 50 minutes soft limit
        )
        print("✅ Celery configured with Redis")
    except Exception as e:
        print(f"⚠️  Celery initialization failed: {e}")
        celery_app = None
else:
    print("⚠️  REDIS_URL not configured - Celery tasks will not be available")

