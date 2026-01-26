"""Celery configuration."""
from celery.schedules import crontab
from datetime import timedelta

# ============================================================================
# BROKER & RESULT BACKEND CONFIGURATION
# ============================================================================

broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/1"
broker_connection_retry_on_startup = True
broker_connection_retry = True
broker_connection_max_retries = 10

# ============================================================================
# TASK CONFIGURATION
# ============================================================================

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True
task_track_started = True
task_time_limit = 30 * 60  # 30 minutes
task_soft_time_limit = 25 * 60  # 25 minutes

# ============================================================================
# RESULT BACKEND CONFIGURATION
# ============================================================================

result_expires = 3600  # 1 hour
result_persistent = True

# ============================================================================
# WORKER CONFIGURATION
# ============================================================================

worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
worker_disable_rate_limits = False

# ============================================================================
# TASK ROUTES (Queue Assignment)
# ============================================================================

task_routes = {
    "app.services.tasks.time_capture.*": {"queue": "time_capture"},
    "app.services.tasks.invoices.*": {"queue": "invoices"},
    "app.services.tasks.notifications.*": {"queue": "notifications"},
    "app.services.tasks.integrations.*": {"queue": "integrations"},
}

# ============================================================================
# QUEUE CONFIGURATION
# ============================================================================

task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
        "priority": 50,
    },
    "time_capture": {
        "exchange": "time_capture",
        "routing_key": "time_capture.*",
        "priority": 60,
    },
    "invoices": {
        "exchange": "invoices",
        "routing_key": "invoices.*",
        "priority": 70,
    },
    "notifications": {
        "exchange": "notifications",
        "routing_key": "notifications.*",
        "priority": 40,
    },
    "integrations": {
        "exchange": "integrations",
        "routing_key": "integrations.*",
        "priority": 50,
    },
}

# ============================================================================
# CELERY BEAT SCHEDULE (Periodic Tasks)
# ============================================================================

beat_schedule = {
    # ========== TIME CAPTURE TASKS ==========
    "sync-time-entries-hourly": {
        "task": "app.services.tasks.time_capture.sync_time_entries_from_integrations",
        "schedule": crontab(minute=0),  # Every hour at minute 0
        "options": {"queue": "time_capture", "priority": 5},
        "kwargs": {},
    },
    "aggregate-daily-time-entries": {
        "task": "app.services.tasks.time_capture.aggregate_daily_time_entries",
        "schedule": crontab(hour=1, minute=0),  # 1 AM daily
        "options": {"queue": "time_capture", "priority": 7},
        "kwargs": {},
    },

    # ========== INVOICE GENERATION TASKS ==========
    "generate-pending-invoices": {
        "task": "app.services.tasks.invoices.generate_pending_invoices",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
        "options": {"queue": "invoices", "priority": 8},
        "kwargs": {},
    },
    "send-pending-invoices": {
        "task": "app.services.tasks.invoices.send_pending_invoices",
        "schedule": crontab(hour=9, minute=0),  # 9 AM daily (business hours)
        "options": {"queue": "notifications", "priority": 7},
        "kwargs": {},
    },
    "check-overdue-invoices": {
        "task": "app.services.tasks.notifications.check_overdue_invoices",
        "schedule": crontab(hour=10, minute=0),  # 10 AM daily
        "options": {"queue": "notifications", "priority": 6},
        "kwargs": {},
    },
    "send-payment-reminders": {
        "task": "app.services.tasks.invoices.send_payment_reminders",
        "schedule": crontab(hour=11, minute=0),  # 11 AM daily
        "options": {"queue": "notifications", "priority": 5},
        "kwargs": {},
    },

    # ========== INTEGRATION SYNC TASKS ==========
    "sync-google-calendar": {
        "task": "app.services.tasks.integrations.sync_google_calendar",
        "schedule": timedelta(minutes=30),  # Every 30 minutes
        "options": {"queue": "integrations", "priority": 4},
        "kwargs": {},
    },
    "sync-outlook-calendar": {
        "task": "app.services.tasks.integrations.sync_outlook_calendar",
        "schedule": timedelta(minutes=30),  # Every 30 minutes
        "options": {"queue": "integrations", "priority": 4},
        "kwargs": {},
    },
    "sync-slack-status": {
        "task": "app.services.tasks.integrations.sync_slack_status",
        "schedule": timedelta(minutes=15),  # Every 15 minutes
        "options": {"queue": "integrations", "priority": 3},
        "kwargs": {},
    },
    "health-check-integrations": {
        "task": "app.services.tasks.integrations.health_check_integrations",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "integrations", "priority": 2},
        "kwargs": {},
    },

    # ========== EMAIL SUMMARY TASKS ==========
    "send-daily-time-summaries": {
        "task": "app.services.tasks.notifications.send_daily_email_summaries",
        "schedule": crontab(hour=17, minute=0),  # 5 PM daily
        "options": {"queue": "notifications", "priority": 6},
        "kwargs": {},
    },
    "send-weekly-invoice-summary": {
        "task": "app.services.tasks.notifications.send_weekly_invoice_summary",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM
        "options": {"queue": "notifications", "priority": 5},
        "kwargs": {},
    },

    # ========== CLEANUP & MAINTENANCE TASKS ==========
    "cleanup-old-logs": {
        "task": "app.services.tasks.invoices.cleanup_old_tasks",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
        "options": {"queue": "default", "priority": 1},
        "kwargs": {"days": 30},
    },
}
