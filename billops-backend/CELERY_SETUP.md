# Celery Task Queue Setup & Configuration

## Overview

BillOps uses **Celery** with **Redis** as the message broker and result backend for asynchronous task processing. This guide covers setup, configuration, and monitoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│              (app/main.py - API requests)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (enqueue tasks)
┌─────────────────────────────────────────────────────────────┐
│                    Redis (Broker)                           │
│          redis://localhost:6379/0                           │
│         (Message queue, task definitions)                   │
└────────────────────┬────────────────────────────────────────┘
         │                              │
         ▼ (consume tasks)              ▼ (store results)
┌──────────────────────┐    ┌──────────────────────────────┐
│  Celery Worker       │    │  Redis (Result Backend)      │
│  (Process tasks)     │    │  redis://localhost:6379/1    │
│                      │    │  (Task results, state)       │
└──────────────────────┘    └──────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│               Celery Beat (Scheduler)                       │
│    (Periodic task scheduling - separate process)           │
└────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Services

- **Python 3.9+** - Application runtime
- **Redis** - Message broker and result backend
- **PostgreSQL** - Application database

### Installation

```bash
# Install Celery and Redis client
pip install celery redis

# Verify Redis is running
redis-cli ping  # Should return PONG

# Or start Redis (if not running)
redis-server
```

## Configuration

### 1. Redis Setup

Redis uses two databases:
- **Database 0** - Message broker (queue)
- **Database 1** - Result backend (task results)

```bash
# Start Redis (development)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:latest

# Test connection
redis-cli ping
```

### 2. Environment Variables

```bash
# .env
REDIS_URL=redis://localhost:6379/0
REDIS_RESULT_BACKEND=redis://localhost:6379/1
```

### 3. Celery Configuration

**File**: `app/workers/celeryconfig.py`

Key settings:
- **broker_url**: Redis connection for task queue
- **result_backend**: Redis connection for results
- **task_serializer**: JSON serialization
- **timezone**: UTC
- **task_routes**: Queue assignment by task name
- **beat_schedule**: Periodic task definitions

## Running Celery Components

### 1. Celery Worker

Processes tasks from the queue:

```bash
# Basic worker (all queues)
celery -A app.celery_app worker --loglevel=info

# Worker with specific queue
celery -A app.celery_app worker -Q time_capture --loglevel=info

# Multiple workers for different queues
celery -A app.celery_app worker -Q time_capture,invoices -n worker1@%h
celery -A app.celery_app worker -Q notifications,integrations -n worker2@%h

# Worker with concurrency control
celery -A app.celery_app worker --concurrency=4 --loglevel=info
```

### 2. Celery Beat Scheduler

Runs periodic tasks on schedule:

```bash
# Start Celery Beat
celery -A app.celery_app beat --loglevel=info

# Or in production with persistence
celery -A app.celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 3. Combined (Development Only)

For development, run both worker and scheduler together:

```bash
celery -A app.celery_app worker --beat --loglevel=info
```

### 4. Events Monitor

Monitor tasks in real-time:

```bash
celery -A app.celery_app events

# Or use Flower web interface
pip install flower
celery -A app.celery_app flower
# Access at http://localhost:5555
```

## Task Modules

### Time Capture Tasks

**File**: `app/services/tasks/time_capture.py`

```python
from app.services.tasks.time_capture import (
    sync_time_entries_from_integrations,
    aggregate_daily_time_entries,
    validate_time_entries,
    send_time_entry_reminders,
)

# Queue a task
result = sync_time_entries_from_integrations.delay()

# Get result
result.get()  # Blocks until complete
result.id     # Task ID
result.state  # PENDING, STARTED, SUCCESS, FAILURE
```

**Tasks:**
1. `sync_time_entries_from_integrations()` - Sync from Google Calendar, Outlook
2. `aggregate_daily_time_entries()` - Daily aggregation and summaries
3. `validate_time_entries()` - Quality checks
4. `send_time_entry_reminders()` - Send reminders (email/Slack)

### Invoice Tasks

**File**: `app/services/tasks/invoices.py`

```python
from app.services.tasks.invoices import (
    generate_pending_invoices,
    send_pending_invoices,
    send_payment_reminders,
    cleanup_old_tasks,
)

# Generate invoices for a specific month
result = generate_pending_invoices.delay(billing_period="2024-01")
```

**Tasks:**
1. `generate_pending_invoices()` - Auto-generate from time entries
2. `send_pending_invoices()` - Send draft invoices to clients
3. `send_payment_reminders()` - Send payment reminders
4. `cleanup_old_tasks()` - Maintenance and cleanup

### Notification Tasks

**File**: `app/services/tasks/notifications.py`

```python
from app.services.tasks.notifications import (
    send_invoice_email,
    send_payment_email,
    check_overdue_invoices,
    send_daily_email_summaries,
)

# Send invoice email
result = send_invoice_email.delay(
    invoice_id="550e8400-e29b-41d4-a716-446655440000",
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
)
```

**Tasks:**
1. `send_invoice_email()` - Invoice delivery
2. `send_payment_email()` - Payment notifications
3. `check_overdue_invoices()` - Overdue invoice detection
4. `send_daily_email_summaries()` - Daily summaries
5. `send_weekly_invoice_summary()` - Weekly stats

### Integration Sync Tasks

**File**: `app/services/tasks/integrations.py`

```python
from app.services.tasks.integrations import (
    sync_google_calendar,
    sync_outlook_calendar,
    sync_slack_status,
    health_check_integrations,
)

# Sync calendar for specific user
result = sync_google_calendar.delay(user_id="user-123")
```

**Tasks:**
1. `sync_google_calendar()` - Google Calendar sync
2. `sync_outlook_calendar()` - Outlook/Microsoft Calendar sync
3. `sync_slack_status()` - Slack status tracking
4. `health_check_integrations()` - Integration health checks

## Periodic Tasks Schedule

Configured in `app/workers/celeryconfig.py`:

### Time Capture
- **Hourly**: Sync time entries from integrations
- **Daily (1 AM)**: Aggregate daily time entries

### Invoices
- **Daily (2 AM)**: Generate pending invoices
- **Daily (9 AM)**: Send pending invoices
- **Daily (10 AM)**: Check overdue invoices
- **Daily (11 AM)**: Send payment reminders
- **Daily (3 AM)**: Cleanup old tasks

### Notifications
- **Daily (5 PM)**: Send daily time summaries
- **Weekly (Monday 9 AM)**: Weekly invoice summary

### Integrations
- **Every 30 minutes**: Sync Google Calendar
- **Every 30 minutes**: Sync Outlook Calendar
- **Every 15 minutes**: Sync Slack status
- **Hourly**: Health check integrations

## Queue Configuration

Tasks are routed to specific queues based on `task_routes`:

```python
task_routes = {
    "app.services.tasks.time_capture.*": {"queue": "time_capture"},
    "app.services.tasks.invoices.*": {"queue": "invoices"},
    "app.services.tasks.notifications.*": {"queue": "notifications"},
    "app.services.tasks.integrations.*": {"queue": "integrations"},
}
```

Each queue has priority settings:
- **notifications**: Priority 40 (Low)
- **integrations**: Priority 50 (Low)
- **default**: Priority 50 (Low)
- **time_capture**: Priority 60 (Medium)
- **invoices**: Priority 70 (High)

## Task Execution

### Queuing a Task

```python
from app.services.tasks.invoices import generate_pending_invoices

# Queue immediately (async)
result = generate_pending_invoices.delay()

# Queue with delay
result = generate_pending_invoices.apply_async(
    countdown=3600  # Execute in 1 hour
)

# Queue with specific queue
result = generate_pending_invoices.apply_async(
    queue="invoices"
)

# Queue with ETA (execute at specific time)
result = generate_pending_invoices.apply_async(
    eta=datetime.now(timezone.utc) + timedelta(hours=1)
)
```

### Checking Task Status

```python
from app.celery_app import celery_app

# Get task result
task_id = "550e8400-e29b-41d4-a716-446655440000"
result = celery_app.AsyncResult(task_id)

# Check state
print(result.state)      # PENDING, STARTED, SUCCESS, FAILURE, RETRY
print(result.result)     # Task return value
print(result.info)       # Progress or error info

# Block until complete
result.get(timeout=30)

# Get without blocking
if result.ready():
    print(result.result)
```

### Error Handling & Retries

Tasks have built-in retry logic:

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 60 seconds
)
def my_task(self):
    try:
        # Task logic
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries)  # 60, 120, 240 seconds
        )
```

Exponential backoff prevents overwhelming external services:
- **Retry 1**: 60 seconds
- **Retry 2**: 120 seconds
- **Retry 3**: 240 seconds

## Monitoring

### 1. Command Line

```bash
# View active tasks
celery -A app.celery_app inspect active

# View pending tasks
celery -A app.celery_app inspect reserved

# View registered tasks
celery -A app.celery_app inspect registered

# View worker stats
celery -A app.celery_app inspect stats

# Revoke a task
celery -A app.celery_app revoke TASK_ID
```

### 2. Flower Web Dashboard

```bash
# Start Flower
pip install flower
celery -A app.celery_app flower

# Access at http://localhost:5555
# Monitor:
# - Active tasks
# - Task history
# - Worker status
# - Task execution time
# - Success/failure rates
```

### 3. Redis Monitoring

```bash
# Monitor Redis commands
redis-cli MONITOR

# Check queue size
redis-cli LLEN celery

# Check keys
redis-cli KEYS *

# Flush Redis (WARNING: clears all data)
redis-cli FLUSHDB
```

### 4. Application Logging

Tasks log to application logs:

```bash
# View task logs
tail -f logs/app.log | grep "app.services.tasks"

# Filter by task type
tail -f logs/app.log | grep "time_capture"
tail -f logs/app.log | grep "invoices"
tail -f logs/app.log | grep "notifications"
```

## Production Deployment

### Using Systemd

Create `/etc/systemd/system/billops-celery-worker.service`:

```ini
[Unit]
Description=BillOps Celery Worker
After=network.target

[Service]
Type=forking
User=billops
Group=billops
WorkingDirectory=/opt/billops
ExecStart=/opt/billops/venv/bin/celery -A app.celery_app worker \
    --loglevel=info \
    --logfile=/var/log/billops/celery-worker.log \
    --pidfile=/var/run/billops/celery-worker.pid \
    --concurrency=4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/billops-celery-beat.service`:

```ini
[Unit]
Description=BillOps Celery Beat Scheduler
After=network.target

[Service]
Type=simple
User=billops
Group=billops
WorkingDirectory=/opt/billops
ExecStart=/opt/billops/venv/bin/celery -A app.celery_app beat \
    --loglevel=info \
    --logfile=/var/log/billops/celery-beat.log \
    --scheduler celery_beat:PersistentScheduler \
    --pidfile=/var/run/billops/celery-beat.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Using Docker

```dockerfile
# Dockerfile.celery
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Worker
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]

# Beat (change CMD)
CMD ["celery", "-A", "app.celery_app", "beat", "--loglevel=info"]
```

### Redis Configuration

For production, configure Redis persistence:

```conf
# redis.conf
save 900 1      # Save if 900 seconds and 1 key changed
save 300 10     # Save if 300 seconds and 10 keys changed
save 60 10000   # Save if 60 seconds and 10000 keys changed

appendonly yes  # Enable AOF persistence
appendfsync everysec  # Fsync every second
```

## Troubleshooting

### Tasks Not Running

1. **Check if worker is running**
   ```bash
   ps aux | grep celery
   ```

2. **Check Redis connection**
   ```bash
   redis-cli ping  # Should return PONG
   ```

3. **Check queue**
   ```bash
   celery -A app.celery_app inspect active
   ```

4. **Check logs**
   ```bash
   tail -f logs/app.log | grep celery
   ```

### Tasks Failing

1. **Get task details**
   ```bash
   celery -A app.celery_app inspect registered | grep TASK_NAME
   ```

2. **Get error info**
   ```python
   from app.celery_app import celery_app
   result = celery_app.AsyncResult("TASK_ID")
   print(result.info)  # Error message
   ```

3. **Revoke stuck task**
   ```bash
   celery -A app.celery_app revoke TASK_ID
   ```

### Redis Issues

```bash
# Check Redis memory
redis-cli INFO memory

# Clear expired keys
redis-cli EVICT ALLKEYS_LRU 100

# Monitor commands
redis-cli MONITOR
```

## Best Practices

1. **Use Celery Tasks for Long Operations**
   - Heavy computations
   - External API calls
   - Database operations
   - File I/O

2. **Keep Tasks Idempotent**
   - Same input = same result
   - Safe to retry
   - Handle duplicate execution

3. **Monitor Task Execution**
   - Use Flower dashboard
   - Set up alerts
   - Log important events
   - Track success rates

4. **Configure Appropriate Timeouts**
   ```python
   @celery_app.task(
       time_limit=30*60,      # Hard limit: 30 minutes
       soft_time_limit=25*60, # Soft limit: 25 minutes
   )
   ```

5. **Use Task Priorities**
   - Higher priority for critical tasks
   - Lower priority for background work
   - Prevents queue saturation

6. **Scale Workers Based on Load**
   - Monitor queue depth
   - Adjust concurrency
   - Use multiple workers for CPU-bound tasks
   - Use prefetch for I/O-bound tasks

7. **Regular Maintenance**
   - Clear old task results
   - Monitor Redis memory
   - Archive task logs
   - Review periodic task schedules

## API Integration

Queue tasks from API endpoints:

```python
from fastapi import APIRouter
from app.services.tasks.invoices import generate_pending_invoices

router = APIRouter()

@router.post("/invoices/generate")
async def trigger_invoice_generation(period: str = None):
    """Trigger invoice generation."""
    result = generate_pending_invoices.delay(billing_period=period)
    return {"task_id": result.id, "status": "queued"}

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    from app.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.ready() else None,
    }
```

## Performance Tuning

### Worker Concurrency

```bash
# For CPU-bound tasks
celery -A app.celery_app worker --concurrency=CPU_COUNT

# For I/O-bound tasks
celery -A app.celery_app worker --concurrency=CPU_COUNT*4

# With prefetch
celery -A app.celery_app worker --prefetch-multiplier=4
```

### Queue Optimization

```python
# In celeryconfig.py
worker_prefetch_multiplier = 4  # Prefetch 4 tasks per worker
worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks
```

## See Also

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Monitoring](https://flower.readthedocs.io/)
- Task modules: `app/services/tasks/*`
- Configuration: `app/workers/celeryconfig.py`
