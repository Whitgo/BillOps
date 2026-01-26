# Celery & Redis - Quick Reference

## Quick Start

### 1. Start Redis
```bash
redis-server
# or
docker run -d -p 6379:6379 redis:latest
```

### 2. Start Celery Worker
```bash
celery -A app.celery_app worker --loglevel=info
```

### 3. Start Celery Beat (Scheduler)
```bash
celery -A app.celery_app beat --loglevel=info
```

### 4. (Development Only) Combined Worker + Beat
```bash
celery -A app.celery_app worker --beat --loglevel=info
```

### 5. Monitor with Flower
```bash
pip install flower
celery -A app.celery_app flower
# Open http://localhost:5555
```

## Key Files

| File | Purpose |
|------|---------|
| `app/celery_app.py` | Celery app initialization |
| `app/workers/celeryconfig.py` | Configuration & schedules |
| `app/services/tasks/time_capture.py` | Time tracking tasks |
| `app/services/tasks/invoices.py` | Invoice generation tasks |
| `app/services/tasks/notifications.py` | Email/Slack tasks |
| `app/services/tasks/integrations.py` | Calendar/integration syncs |

## Common Commands

### Worker Management
```bash
# Start worker
celery -A app.celery_app worker --loglevel=info

# Start specific queue
celery -A app.celery_app worker -Q invoices --loglevel=info

# Multiple workers
celery -A app.celery_app worker -Q time_capture -n worker1@%h
celery -A app.celery_app worker -Q invoices -n worker2@%h

# With concurrency
celery -A app.celery_app worker --concurrency=4 --loglevel=info
```

### Task Inspection
```bash
# View active tasks
celery -A app.celery_app inspect active

# View pending tasks
celery -A app.celery_app inspect reserved

# View registered tasks
celery -A app.celery_app inspect registered

# View worker stats
celery -A app.celery_app inspect stats
```

### Task Control
```bash
# Revoke a task
celery -A app.celery_app revoke TASK_ID

# Revoke with terminate
celery -A app.celery_app revoke TASK_ID --terminate

# Purge all pending tasks
celery -A app.celery_app purge
```

### Monitoring
```bash
# Real-time events
celery -A app.celery_app events

# Flower dashboard
celery -A app.celery_app flower
```

## Queue Tasks

### From Python Code

```python
from app.services.tasks.invoices import generate_pending_invoices
from app.services.tasks.time_capture import sync_time_entries_from_integrations
from app.services.tasks.notifications import send_invoice_email

# Queue immediately
result = generate_pending_invoices.delay()

# Queue with delay (30 minutes)
result = generate_pending_invoices.apply_async(countdown=1800)

# Queue with specific time
from datetime import datetime, timedelta, timezone
eta = datetime.now(timezone.utc) + timedelta(hours=1)
result = generate_pending_invoices.apply_async(eta=eta)

# Get task ID
task_id = result.id

# Get result later
print(result.get())  # Blocks until complete
```

### From API Endpoint

```python
from fastapi import APIRouter
from app.services.tasks.invoices import generate_pending_invoices

@router.post("/tasks/generate-invoices")
async def trigger_generation(period: str = None):
    result = generate_pending_invoices.delay(billing_period=period)
    return {"task_id": result.id}

@router.get("/tasks/{task_id}")
async def get_status(task_id: str):
    from app.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    return {"state": result.state, "result": result.result}
```

## Periodic Tasks

Scheduled in `app/workers/celeryconfig.py`:

### View Schedule
```bash
# List all periodic tasks
celery -A app.celery_app inspect scheduled
```

### Common Schedules

```python
from celery.schedules import crontab
from datetime import timedelta

# Every hour
"schedule": crontab(minute=0)

# Every day at 9 AM
"schedule": crontab(hour=9, minute=0)

# Every Monday at 9 AM
"schedule": crontab(day_of_week=1, hour=9, minute=0)

# Every 30 minutes
"schedule": timedelta(minutes=30)

# Every 15 minutes
"schedule": timedelta(minutes=15)
```

## Task Status States

| State | Meaning |
|-------|---------|
| PENDING | Task not yet executed |
| STARTED | Task has started |
| SUCCESS | Task completed successfully |
| FAILURE | Task raised an exception |
| RETRY | Task is being retried |
| REVOKED | Task was revoked/cancelled |

## Check Task Status

```python
from app.celery_app import celery_app

result = celery_app.AsyncResult("TASK_ID")

# State
print(result.state)      # Current state
print(result.ready())    # Is complete?
print(result.failed())   # Did it fail?
print(result.successful())  # Did it succeed?

# Result
print(result.result)     # Return value
print(result.info)       # Progress info or error

# Get with timeout
try:
    value = result.get(timeout=30)
except Exception as e:
    print(f"Task failed: {e}")
```

## Configuration

### Redis Connection

```python
# In app/config/settings.py
redis_url = "redis://localhost:6379/0"      # Broker (queue)
redis_result_backend = "redis://localhost:6379/1"  # Results
```

### Task Settings

```python
# In app/workers/celeryconfig.py
task_serializer = "json"           # Data format
task_track_started = True          # Track task start
task_time_limit = 30 * 60          # Hard limit: 30 mins
task_soft_time_limit = 25 * 60     # Soft limit: 25 mins
```

### Queues

```python
# Route tasks to specific queues
task_routes = {
    "app.services.tasks.invoices.*": {"queue": "invoices"},
    "app.services.tasks.notifications.*": {"queue": "notifications"},
}

# Queue priority
task_queues = {
    "invoices": {"priority": 70},      # High priority
    "notifications": {"priority": 40}, # Low priority
}
```

## Troubleshooting

### Check Redis
```bash
# Verify Redis is running
redis-cli ping              # Should return PONG

# Check memory usage
redis-cli INFO memory

# Clear all data (WARNING!)
redis-cli FLUSHDB
```

### Check Worker
```bash
# Is worker running?
ps aux | grep celery

# Check worker status
celery -A app.celery_app inspect active

# View worker logs
tail -f logs/app.log | grep celery
```

### Task Not Running
1. Verify Redis: `redis-cli ping`
2. Verify worker: `ps aux | grep celery`
3. Check queue: `celery -A app.celery_app inspect active`
4. Check logs: `tail -f logs/app.log`

### Task Failing
1. Get task result: `celery -A app.celery_app inspect active`
2. Check error: 
   ```python
   result = celery_app.AsyncResult("TASK_ID")
   print(result.info)  # Error message
   ```
3. Review logs: `tail -f logs/app.log | grep TASK_NAME`

## Task Examples

### Time Capture Tasks

```python
from app.services.tasks.time_capture import (
    sync_time_entries_from_integrations,
    aggregate_daily_time_entries,
)

# Sync calendar events
result = sync_time_entries_from_integrations.delay()

# Aggregate daily
result = aggregate_daily_time_entries.delay()
```

### Invoice Tasks

```python
from app.services.tasks.invoices import (
    generate_pending_invoices,
    send_pending_invoices,
    send_payment_reminders,
)

# Generate invoices for January 2024
result = generate_pending_invoices.delay(billing_period="2024-01")

# Send pending invoices
result = send_pending_invoices.delay()

# Send payment reminders (7 days before due)
result = send_payment_reminders.delay(days_before_due=7)
```

### Notification Tasks

```python
from app.services.tasks.notifications import (
    send_invoice_email,
    send_payment_email,
    check_overdue_invoices,
)

# Send invoice email
result = send_invoice_email.delay(
    invoice_id="550e8400-e29b-41d4-a716-446655440000",
    recipient_email="client@example.com",
    recipient_name="Acme Corp",
)

# Check overdue invoices
result = check_overdue_invoices.delay()
```

### Integration Tasks

```python
from app.services.tasks.integrations import (
    sync_google_calendar,
    sync_slack_status,
    health_check_integrations,
)

# Sync Google Calendar for user
result = sync_google_calendar.delay(user_id="user-123")

# Sync Slack status
result = sync_slack_status.delay()

# Health check
result = health_check_integrations.delay()
```

## Monitoring Tools

### Command Line Tools

```bash
# Celery inspect
celery -A app.celery_app inspect active
celery -A app.celery_app inspect reserved
celery -A app.celery_app inspect registered

# Celery events
celery -A app.celery_app events
```

### Flower Web Dashboard

```bash
# Start Flower
pip install flower
celery -A app.celery_app flower

# Access http://localhost:5555
# Monitor:
# - Active tasks in real-time
# - Task execution history
# - Worker pool status
# - Task success/failure rates
# - Execution time graphs
```

### Redis CLI

```bash
# Check queue size
redis-cli LLEN celery

# Monitor Redis commands
redis-cli MONITOR

# Check all keys
redis-cli KEYS *

# Get key value
redis-cli GET key_name
```

## Performance Tips

1. **Use appropriate worker count**
   ```bash
   celery -A app.celery_app worker --concurrency=4
   ```

2. **Set prefetch multiplier**
   ```bash
   # In celeryconfig.py
   worker_prefetch_multiplier = 4
   ```

3. **Use specific queues for worker**
   ```bash
   celery -A app.celery_app worker -Q invoices
   ```

4. **Scale with multiple workers**
   ```bash
   # Terminal 1
   celery -A app.celery_app worker -Q time_capture -n w1@%h
   
   # Terminal 2
   celery -A app.celery_app worker -Q invoices -n w2@%h
   
   # Terminal 3
   celery -A app.celery_app beat
   ```

5. **Monitor with Flower**
   ```bash
   celery -A app.celery_app flower  # http://localhost:5555
   ```

## See Also

- Full Documentation: [CELERY_SETUP.md](CELERY_SETUP.md)
- Task Modules: `app/services/tasks/`
- Configuration: `app/workers/celeryconfig.py`
- Celery Docs: https://docs.celeryproject.org/
- Redis Docs: https://redis.io/docs/
