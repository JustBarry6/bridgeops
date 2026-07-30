from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "bridgeops",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Importé ici pour que Celery enregistre les tâches au démarrage du worker.
from app.workers import tasks  # noqa: F401