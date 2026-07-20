from celery import Celery
from celery.schedules import crontab
#from datetime import timedelta

from app.core.config import settings

celery_app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL
)

celery_app.conf.update(
    
)
celery_app.conf.beat_schedule = {}#{
#    "recalculate-apps-rating": {
#        "task": "tasks.calculate_apps_rating",
#        "schedule": crontab(hour="*/1")
#    }
#}