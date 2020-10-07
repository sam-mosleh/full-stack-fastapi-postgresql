from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker", broker=settings.CELERY_REDIS_DSN, backend=settings.CELERY_REDIS_DSN
)

celery_app.conf.task_routes = {"app.worker.test_celery": "main-queue"}
