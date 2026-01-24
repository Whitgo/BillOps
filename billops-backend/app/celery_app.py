from celery import Celery

celery = Celery(
    "billops",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery.conf.task_routes = {
    "tasks.ingest.*": {"queue": "ingest"},
    "tasks.billing.*": {"queue": "billing"},
    "tasks.notifications.*": {"queue": "notifications"},
}
