"""Celery application initialization."""
import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import logging

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery("billops")

# Load configuration from celeryconfig module
celery_app.config_from_object("app.workers.celeryconfig")

# Auto-discover tasks from all registered apps
celery_app.autodiscover_tasks([
    "app.services.tasks.time_capture",
    "app.services.tasks.invoices",
    "app.services.tasks.notifications",
    "app.services.tasks.integrations",
    "app.services.tasks.billing",
    "app.services.tasks.calendar_sync",
])

# ============================================================================
# SIGNAL HANDLERS FOR MONITORING
# ============================================================================

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log when a task starts."""
    logger.info(f"Task {task.name} [{task_id}] started")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, result=None, **kwargs):
    """Log when a task completes successfully."""
    logger.info(f"Task {task.name} [{task_id}] completed successfully")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log when a task fails."""
    logger.error(f"Task {sender.name} [{task_id}] failed with exception: {exception}", exc_info=True)


# Ensure backwards compatibility
celery = celery_app
