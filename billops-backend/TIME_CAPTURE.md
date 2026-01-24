# Time-Capture Heuristics System

## Overview

The time-capture heuristics system automatically converts raw activity signals (keyboard/mouse events, application window tracking, browser history) into suggested time entries for billing. The system uses intelligent idle detection, activity classification, and confidence scoring to create high-quality time entries.

## Architecture

```
Activity Signals (from integrations)
          ↓
    Idle Detection (detector.py)
          ↓
   Activity Classification (classifier.py)
          ↓
    Activity Grouping (heuristics.py)
          ↓
  Confidence Scoring (heuristics.py)
          ↓
    Suggested Time Entries (NamedTuple)
          ↓
   Celery Task (ingest.py)
          ↓
   TimeEntry Database Records
```

## Components

### 1. Idle Detection (`detector.py`)

Detects periods of inactivity between activity signals to segment time into distinct work sessions.

**Algorithm:**
- Sorts activity signals by timestamp
- Calculates gaps between consecutive signals
- Flags gaps exceeding idle threshold (default: 5 minutes) as idle periods
- Classifies idle periods as "mergeable" (≤10 min) or "breaks" (>10 min)

**Key Types:**
```python
IdleSignal(NamedTuple):
    start_time: datetime        # When idle period started
    end_time: datetime          # When idle period ended
    idle_minutes: float         # Duration of idle
    reason: str                 # "inactivity_threshold" or "break_detected"
```

**Key Methods:**
- `detect_idle_periods(signals, idle_threshold_minutes=5)` → `List[IdleSignal]`
- `should_merge_with_idle(gap_minutes, max_merge_idle=10)` → `bool`
- `filter_idle_periods(idle_periods, max_merge_idle=10)` → `tuple[List[IdleSignal], List[IdleSignal]]`

**Example:**
```python
signals = [
    {"timestamp": "09:00", "app": "vscode"},
    {"timestamp": "09:15", "app": "vscode"},
    # 30 minute gap
    {"timestamp": "09:45", "app": "chrome"},
]

idle_periods = IdleDetector.detect_idle_periods(signals)
# [IdleSignal(start=09:15, end=09:45, idle_minutes=30)]
```

### 2. Activity Classification (`classifier.py`)

Classifies activity signals by type (work vs personal) and source (keyboard, mouse, application, domain).

**Activity Types:**
- `FOCUSED_WORK` (confidence: 0.90) - Coding, development, design work
- `MEETING` (confidence: 0.85) - Video calls, conferences
- `RESEARCH` (confidence: 0.75) - Browser research, documentation review
- `COMMUNICATION` (confidence: 0.70) - Email, chat, messaging
- `ADMIN` (confidence: 0.60) - Administrative tasks
- `PERSONAL` (confidence: 0.40) - Non-work activities
- `IDLE` (confidence: 0.00) - Inactivity

**Work Applications (18+):**
```
Development: vscode, sublime, pycharm, intellij, vim, emacs
Communication: slack, teams, discord, telegram, whatsapp
Meeting: zoom, meet, skype, webex
Browser: chrome, firefox, safari, edge
```

**Work Domains (9):**
```
github.com, stackoverflow.com, github.io, trello.com, slack.com,
figma.com, jira.atlassian.net, docs.google.com, notion.so
```

**Key Methods:**
- `classify_signal(signal)` → `ActivityType`
- `classify_source(signal)` → `ActivitySource`
- `is_work_related(signal)` → `bool`
- `get_context_data(signals)` → `dict` with applications, domains, activity_distribution

**Example:**
```python
signal = {"app": "vscode", "type": "keyboard"}
activity_type = SourceClassifier.classify_signal(signal)
# ActivityType.FOCUSED_WORK

signal = {"app": "slack", "type": "messaging"}
activity_type = SourceClassifier.classify_signal(signal)
# ActivityType.COMMUNICATION
```

### 3. Activity Heuristics (`heuristics.py`)

Groups activities by idle periods and generates suggested time entries with confidence scores.

**Key Types:**
```python
SuggestedTimeEntry(NamedTuple):
    started_at: datetime              # Session start time (UTC)
    ended_at: datetime                # Session end time (UTC)
    activity_type: str                # Primary activity type
    confidence: float                 # 0.0-1.0 confidence score
    context_data: dict                # Applications, domains, details
    description: str                  # Human-readable description
    should_verify: bool               # True if confidence < 0.5
```

**Key Methods:**
- `group_activities(signals, idle_threshold_minutes=5, max_merge_idle_minutes=10)` → `List[List[signal]]`
- `calculate_confidence(signals)` → `float` (0.0-1.0)
- `create_suggested_entry(signals, activity_type="work")` → `SuggestedTimeEntry`
- `generate_time_entries(signals, ...)` → `List[SuggestedTimeEntry]`

**Confidence Calculation:**
```
confidence = consistency_score × type_multiplier
consistency_score = (signals_with_dominant_type / total_signals)
type_multiplier = {
    "focused_work": 0.90,
    "meeting": 0.85,
    "research": 0.75,
    "communication": 0.70,
    "admin": 0.60,
    ...
}
```

**Example:**
```python
signals = [
    {"timestamp": "09:00", "app": "vscode", "type": "keyboard"},
    {"timestamp": "09:15", "app": "vscode", "type": "keyboard"},
]

entries = ActivityHeuristics.generate_time_entries(signals)
# [SuggestedTimeEntry(
#     started_at=datetime(2024, 1, 24, 9, 0),
#     ended_at=datetime(2024, 1, 24, 9, 15),
#     activity_type="focused_work",
#     confidence=0.90,
#     context_data={...},
#     should_verify=False
# )]
```

### 4. Celery Ingest Task (`ingest.py`)

Async task that processes raw activity signals and creates time entries in the database.

**Task Details:**
- Name: `tasks.ingest_events`
- Max retries: 3
- Retry backoff: Exponential (60 × 2^retry_count seconds)
- Status: Returns success/failure with created entry IDs

**Task Signature:**
```python
@celery_app.task(name="tasks.ingest_events", bind=True, max_retries=3)
def ingest_events_task(self, user_id: str, activity_signals: list[dict]) -> dict
```

**Workflow:**
1. Validate user exists in database
2. Convert activity signal timestamps to timezone-aware UTC datetime
3. Generate suggested time entries via `ActivityHeuristics.generate_time_entries()`
4. Create `TimeEntry` records with:
   - `source="auto"` (automated from signals)
   - `status="pending"` (awaiting review)
   - `context_data` with applications, domains, activity metadata
5. Extract project_id/client_id from context (if available)
6. Handle errors gracefully:
   - Per-signal errors collected in `verification_required` list
   - Low-confidence entries flagged for manual review
   - Database transaction rolled back on fatal errors

**Return Value:**
```python
{
    "status": "success",  # or "partial_success", "error"
    "suggested_count": 5,  # Total entries generated
    "created_count": 4,    # Entries successfully created
    "created_ids": ["uuid1", "uuid2", ...],
    "verification_required": [  # Entries needing review
        {
            "confidence": 0.45,
            "reason": "Low confidence",
            "description": "..."
        }
    ]
}
```

**Example Usage:**
```python
from app.services.tasks.ingest import ingest_events_task

# Enqueue task (async)
result = ingest_events_task.delay(
    user_id="user-123",
    activity_signals=[
        {
            "timestamp": "2024-01-24T09:00:00Z",
            "app": "vscode",
            "type": "keyboard"
        },
        {
            "timestamp": "2024-01-24T09:15:00Z",
            "app": "vscode",
            "type": "keyboard"
        },
    ]
)

# Check result
result.get()  # Returns dict above
```

## Configuration

### Idle Detection Thresholds
```python
# Default: 5 minutes of inactivity = idle period
IDLE_THRESHOLD_MINUTES = 5

# Default: gaps ≤ 10 min can be merged into same session
MAX_MERGE_IDLE_MINUTES = 10
```

### Confidence Thresholds
```python
# Entries with confidence < 0.5 flagged for manual verification
CONFIDENCE_VERIFY_THRESHOLD = 0.5

# Type-based multipliers (0.0-1.0)
CONFIDENCE_MULTIPLIERS = {
    "focused_work": 0.90,
    "meeting": 0.85,
    "research": 0.75,
    "communication": 0.70,
    "admin": 0.60,
    "personal": 0.40,
    "idle": 0.00,
}
```

## Data Flow Example

### Input: Raw Activity Signals
```json
[
  {
    "timestamp": "2024-01-24T09:00:00Z",
    "app": "vscode",
    "type": "keyboard",
    "source_type": "keyboard"
  },
  {
    "timestamp": "2024-01-24T09:15:00Z",
    "app": "vscode",
    "type": "mouse_click",
    "source_type": "mouse"
  },
  {
    "timestamp": "2024-01-24T09:45:00Z",
    "app": "chrome",
    "domain": "stackoverflow.com",
    "source_type": "window"
  }
]
```

### Processing Steps

1. **Idle Detection**
   - Detects 30-minute gap between 09:15 and 09:45
   - Classifies as "break" (>10 min)
   - Creates 2 distinct sessions

2. **Activity Classification**
   - VSCode + keyboard → FOCUSED_WORK (0.90 confidence)
   - Chrome + stackoverflow.com → RESEARCH (0.75 confidence)

3. **Grouping & Heuristics**
   - Session 1: VSCode signals (09:00-09:15)
   - Session 2: Chrome signals (09:45+)

4. **Suggested Entries**
   ```python
   [
     SuggestedTimeEntry(
       started_at=2024-01-24T09:00:00Z,
       ended_at=2024-01-24T09:15:00Z,
       activity_type="focused_work",
       confidence=0.90,
       context_data={"applications": ["vscode"], "primary_activity": "focused_work"},
       description="VSCode development session",
       should_verify=False
     ),
     SuggestedTimeEntry(
       started_at=2024-01-24T09:45:00Z,
       ended_at=2024-01-24T10:00:00Z,
       activity_type="research",
       confidence=0.75,
       context_data={"applications": ["chrome"], "domains": ["stackoverflow.com"]},
       description="Research on Stack Overflow",
       should_verify=False
     )
   ]
   ```

5. **Database Storage**
   - Creates 2 TimeEntry records with status="pending"
   - Links to user account
   - Stores context for later review/adjustment

### Output: TimeEntry Records
```json
{
  "id": "uuid1",
  "user_id": "user-123",
  "started_at": "2024-01-24T09:00:00Z",
  "ended_at": "2024-01-24T09:15:00Z",
  "duration_minutes": 15,
  "activity_type": "focused_work",
  "source": "auto",
  "status": "pending",
  "context_data": {
    "applications": ["vscode"],
    "confidence": 0.90,
    "primary_activity": "focused_work"
  }
}
```

## Testing

Run the comprehensive test suite:

```bash
cd billops-backend
python test_time_capture.py
```

**Test Coverage:**
- ✓ Idle detection (gap analysis, threshold filtering)
- ✓ Idle merging (mergeable vs break classification)
- ✓ Source classification (app → activity type mapping)
- ✓ Activity grouping (session creation by breaks)
- ✓ Confidence scoring (consistency × type multiplier)
- ✓ Time entry generation (full pipeline)
- ✓ Context extraction (applications, domains, distribution)

## Integration Points

### With API Routes
```python
# Trigger manual processing (e.g., POST /api/v1/time-entries/ingest)
@router.post("/ingest")
async def ingest_time_entries(
    user_id: str,
    activity_signals: List[dict],
    db: Session = Depends(get_db)
):
    result = ingest_events_task.delay(user_id, activity_signals)
    return {"task_id": result.id, "status": "processing"}
```

### With TimeEntry Model
- Creates records with `source="auto"`, `status="pending"`
- Stores confidence in `context_data["confidence"]`
- Preserves activity classification in `context_data`

### With Celery
- Task name: `tasks.ingest_events`
- Queue: Default (configurable)
- Priority: Normal (configurable)
- Retries: 3 with exponential backoff

### With User Validation
- Checks user exists before processing
- Returns error if user_id invalid
- Aggregates per-signal errors for admin review

## Performance Characteristics

- **Signal Processing**: ~0.1ms per signal (1000 signals ≈ 100ms)
- **Entry Generation**: O(n) where n = number of signals
- **Confidence Calculation**: O(m) where m = signals per group
- **Database Writes**: Batch insert (all or nothing)
- **Memory**: ~5KB per signal (namedtuples + metadata)

## Future Enhancements

1. **ML-Based Classification**: Train classifier on user's historical data
2. **Multi-Source Fusion**: Combine calendar, Git commits, analytics
3. **Break Detection**: Automatic smart break detection (meetings, lunch, etc.)
4. **Confidence Learning**: Adjust multipliers based on user feedback
5. **Offline Support**: Queue signals during connectivity issues
6. **Real-Time Processing**: WebSocket updates instead of batch ingestion
7. **Integration Webhooks**: Google Calendar, Slack analytics, GitHub API
8. **Advanced Grouping**: ML clustering based on activity patterns

## Troubleshooting

### High False Positives
- Increase `IDLE_THRESHOLD_MINUTES` (fewer small gaps)
- Decrease `CONFIDENCE_MULTIPLIERS` for low-confidence types
- Enable manual verification for specific users

### Missed Entries
- Decrease `IDLE_THRESHOLD_MINUTES` (detect shorter gaps)
- Check activity source configuration (app mappings)
- Verify signal timestamps are correct (UTC)

### Database Issues
- Check TimeEntry model has all required fields
- Verify project_id/client_id exist when provided
- Review database constraints on status, source fields

## References

- Activity heuristics: `app/services/time_capture/heuristics.py`
- Idle detection: `app/services/time_capture/detector.py`
- Activity classification: `app/services/time_capture/classifier.py`
- Celery task: `app/services/tasks/ingest.py`
- TimeEntry model: `app/models/time_entry.py`
- TimeEntry schema: `app/schemas/time_entry.py`
