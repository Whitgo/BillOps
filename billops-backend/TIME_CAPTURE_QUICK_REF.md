# Time-Capture Quick Reference

## Module Overview

| Module | Purpose | Key Classes |
|--------|---------|------------|
| `detector.py` | Idle period detection | `IdleDetector`, `IdleSignal` |
| `classifier.py` | Activity type classification | `SourceClassifier`, `ActivityType`, `ActivitySource` |
| `heuristics.py` | Activity grouping & scoring | `ActivityHeuristics`, `SuggestedTimeEntry` |
| `ingest.py` | Celery task for processing | `ingest_events_task` |
| `__init__.py` | Module exports | All public classes |

## Common Operations

### Detect Idle Periods
```python
from app.services.time_capture import IdleDetector

idle_periods = IdleDetector.detect_idle_periods(
    signals=activity_signals,
    idle_threshold_minutes=5
)
```

### Classify Activity
```python
from app.services.time_capture import SourceClassifier, ActivityType

activity_type = SourceClassifier.classify_signal(signal)
# Returns: ActivityType.FOCUSED_WORK, RESEARCH, MEETING, COMMUNICATION, ADMIN, PERSONAL, IDLE

is_work = SourceClassifier.is_work_related(signal)  # Returns bool
```

### Generate Time Entries
```python
from app.services.time_capture import ActivityHeuristics

suggested_entries = ActivityHeuristics.generate_time_entries(
    signals=activity_signals,
    idle_threshold_minutes=5,
    max_merge_idle_minutes=10
)

for entry in suggested_entries:
    print(f"{entry.started_at} - {entry.ended_at}: {entry.activity_type}")
    print(f"  Confidence: {entry.confidence:.2f}")
    if entry.should_verify:
        print(f"  [NEEDS REVIEW]")
```

### Process Activity Signals (Async)
```python
from app.services.tasks.ingest import ingest_events_task

result = ingest_events_task.delay(
    user_id="user-123",
    activity_signals=signals
)

# Check status
status = result.status  # PENDING, SUCCESS, FAILURE
result_data = result.get()  # Block and get result

# Or check later
from celery.result import AsyncResult
result = AsyncResult(task_id)
```

## Activity Type Reference

| Type | Confidence | Apps | Detection |
|------|-----------|------|-----------|
| `FOCUSED_WORK` | 0.90 | VSCode, Sublime, PyCharm, etc. | IDE + keyboard activity |
| `MEETING` | 0.85 | Zoom, Teams, Meet, Skype | Video call apps |
| `RESEARCH` | 0.75 | Chrome, Firefox, Safari | Browser + work domains |
| `COMMUNICATION` | 0.70 | Slack, Teams, Discord, Email | Chat/messaging apps |
| `ADMIN` | 0.60 | File managers, spreadsheets | Administrative tools |
| `PERSONAL` | 0.40 | Entertainment, social media | Non-work apps |
| `IDLE` | 0.00 | (no activity) | Gap ≥ threshold |

## Work Applications (18+)

**Development:** vscode, sublime, pycharm, intellij, vim, emacs

**Communication:** slack, teams, discord, telegram, whatsapp

**Meeting:** zoom, meet, skype, webex

**Browsers:** chrome, firefox, safari, edge

## Work Domains (9)

- github.com
- stackoverflow.com
- github.io
- trello.com
- slack.com
- figma.com
- jira.atlassian.net
- docs.google.com
- notion.so

## Confidence Scoring

```
confidence = consistency_score × type_multiplier

consistency_score = signals_with_dominant_type / total_signals
type_multiplier = activity_type_confidence_base
```

**Thresholds:**
- ≥ 0.75: High confidence (auto-approve)
- 0.50-0.75: Medium confidence (review)
- < 0.50: Low confidence (must verify)

## Database Integration

### Create TimeEntry from SuggestedTimeEntry
```python
from app.models.time_entry import TimeEntry

entry = TimeEntry(
    user_id=user_id,
    started_at=suggested_entry.started_at,
    ended_at=suggested_entry.ended_at,
    duration_minutes=int((suggested_entry.ended_at - suggested_entry.started_at).total_seconds() / 60),
    status="pending",  # Awaiting review
    source="auto",     # Auto-generated
    project_id=...,    # Optional
    client_id=...,     # Optional
    context_data=suggested_entry.context_data,
)
db.add(entry)
db.commit()
```

### Update Entry Status
```python
entry.status = "approved"   # or "rejected", "archived"
entry.project_id = project_id
entry.client_id = client_id
db.commit()
```

## Testing

```bash
# Run comprehensive tests
cd billops-backend
python test_time_capture.py

# Expected output:
# ✓ Idle Detection
# ✓ Idle Merging Logic
# ✓ Source Classification
# ✓ Activity Grouping
# ✓ Confidence Scoring
# ✓ Time Entry Generation
# ✓ Context Data Extraction
```

## Troubleshooting

**High False Positives:**
- Increase `IDLE_THRESHOLD_MINUTES` (e.g., 10 instead of 5)
- Check activity source configuration

**Missed Entries:**
- Decrease `IDLE_THRESHOLD_MINUTES` (e.g., 3 instead of 5)
- Verify signal timestamps are UTC

**Low Confidence Scores:**
- Check app mappings in `SourceClassifier.WORK_APPLICATIONS`
- Review `SourceClassifier.WORK_DOMAINS` for missing domains

**Database Errors:**
- Verify TimeEntry model has all fields
- Check project_id and client_id exist
- Review database constraints

## Performance Tips

1. **Batch Signals:** Process signals in batches (100-1000 per task)
2. **Adjust Thresholds:** Increase idle threshold for fewer entries
3. **Use Caching:** Cache app→type mappings in Redis
4. **Async Processing:** Always use Celery for production
5. **Monitor Tasks:** Check Celery worker logs for errors

## API Endpoints

```
POST   /api/v1/time-entries/ingest              # Submit signals
GET    /api/v1/time-entries/ingest/{task_id}   # Check status
GET    /api/v1/time-entries/pending-review      # List pending
PATCH  /api/v1/time-entries/{entry_id}          # Approve/reject
GET    /api/v1/time-entries                     # List all entries
```

## Configuration

```python
# app/config/settings.py
IDLE_THRESHOLD_MINUTES = 5
MAX_MERGE_IDLE_MINUTES = 10
CONFIDENCE_VERIFY_THRESHOLD = 0.5
```

## Dependencies

- Python 3.10+
- FastAPI
- SQLAlchemy (ORM)
- Celery (async tasks)
- Redis (task broker/results)
- datetime.timezone (stdlib)

## File Structure

```
app/
  services/
    time_capture/
      __init__.py           # Module exports
      detector.py          # IdleDetector
      classifier.py        # SourceClassifier
      heuristics.py        # ActivityHeuristics
    tasks/
      ingest.py            # Celery task
  models/
    time_entry.py          # TimeEntry model
  schemas/
    time_entry.py          # TimeEntry schemas
```

## Next Steps

1. ✓ Time-capture heuristics module (idle detection, classification, grouping)
2. ✓ Celery ingest task (signal processing, DB persistence)
3. → API endpoints (ingest, status, review)
4. → Billing engine tasks (invoice generation)
5. → Notification tasks (email, Slack alerts)
6. → Testing & validation (unit, integration, e2e)

## Support

For issues or questions:
- Check `TIME_CAPTURE.md` for detailed documentation
- Review `TIME_CAPTURE_API.md` for API integration
- Run `python test_time_capture.py` to verify setup
- Check logs: `app/logs/` directory
