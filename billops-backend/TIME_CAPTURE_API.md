# Time-Capture API Integration Guide

## Overview

This guide shows how to integrate the time-capture heuristics system into the BillOps API for automated time entry generation from activity signals.

## API Endpoints

### 1. Ingest Activity Signals

**Endpoint:** `POST /api/v1/time-entries/ingest`

**Purpose:** Submit raw activity signals for processing into suggested time entries

**Request:**
```json
{
  "activity_signals": [
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
    }
  ],
  "idle_threshold_minutes": 5,
  "max_merge_idle_minutes": 10
}
```

**Response:**
```json
{
  "status": "processing",
  "task_id": "celery-task-uuid",
  "message": "Activity signals queued for processing"
}
```

**Implementation:**
```python
from fastapi import APIRouter, Depends, BackgroundTasks
from app.schemas.time_entry import TimeEntryCreate
from app.services.tasks.ingest import ingest_events_task
from app.core.security import get_current_user

router = APIRouter(prefix="/time-entries", tags=["time-entries"])

@router.post("/ingest")
async def ingest_activity_signals(
    activity_signals: list[dict],
    idle_threshold_minutes: int = 5,
    max_merge_idle_minutes: int = 10,
    current_user = Depends(get_current_user),
):
    """
    Ingest raw activity signals and generate suggested time entries.
    
    - Processes signals asynchronously via Celery
    - Detects idle periods and groups activities
    - Creates suggested entries with confidence scores
    - Stores pending entries for review
    """
    # Queue async task
    result = ingest_events_task.delay(
        user_id=current_user.id,
        activity_signals=activity_signals,
    )
    
    return {
        "status": "processing",
        "task_id": result.id,
        "message": "Activity signals queued for processing",
    }
```

### 2. Get Ingest Task Status

**Endpoint:** `GET /api/v1/time-entries/ingest/{task_id}`

**Purpose:** Check status of activity signal processing task

**Response (Processing):**
```json
{
  "task_id": "celery-task-uuid",
  "status": "PENDING",
  "message": "Task is queued for processing"
}
```

**Response (Complete):**
```json
{
  "task_id": "celery-task-uuid",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "suggested_count": 5,
    "created_count": 4,
    "created_ids": [
      "entry-uuid-1",
      "entry-uuid-2",
      "entry-uuid-3",
      "entry-uuid-4"
    ],
    "verification_required": [
      {
        "confidence": 0.45,
        "reason": "Low confidence - multiple activity types detected",
        "description": "Mixed VSCode and browser usage"
      }
    ]
  }
}
```

**Implementation:**
```python
from celery.result import AsyncResult

@router.get("/ingest/{task_id}")
async def get_ingest_status(task_id: str):
    """Get status of activity signal ingestion task."""
    result = AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
```

### 3. List Pending Time Entries for Review

**Endpoint:** `GET /api/v1/time-entries/pending-review`

**Purpose:** Get time entries awaiting manual review

**Response:**
```json
{
  "total": 3,
  "entries": [
    {
      "id": "entry-uuid-1",
      "started_at": "2024-01-24T09:00:00Z",
      "ended_at": "2024-01-24T09:45:00Z",
      "duration_minutes": 45,
      "status": "pending",
      "source": "auto",
      "activity_type": "focused_work",
      "context_data": {
        "confidence": 0.45,
        "applications": ["vscode", "chrome"],
        "primary_activity": "mixed"
      }
    }
  ]
}
```

**Implementation:**
```python
@router.get("/pending-review")
async def list_pending_entries(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get time entries pending manual review."""
    entries = db.query(TimeEntry).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.status == "pending",
    ).all()
    
    return {
        "total": len(entries),
        "entries": [TimeEntryResponse.from_orm(e) for e in entries],
    }
```

### 4. Approve/Reject Entry

**Endpoint:** `PATCH /api/v1/time-entries/{entry_id}`

**Purpose:** Review and approve/reject generated time entry

**Request:**
```json
{
  "status": "approved",
  "notes": "Looks good, minor adjustment needed",
  "project_id": "project-uuid",
  "client_id": "client-uuid",
  "activity_type": "research"
}
```

**Response:**
```json
{
  "id": "entry-uuid-1",
  "status": "approved",
  "started_at": "2024-01-24T09:00:00Z",
  "ended_at": "2024-01-24T09:45:00Z",
  "duration_minutes": 45,
  "project_id": "project-uuid",
  "client_id": "client-uuid"
}
```

**Implementation:**
```python
from app.schemas.time_entry import TimeEntryUpdate

@router.patch("/{entry_id}")
async def update_time_entry(
    entry_id: str,
    entry_update: TimeEntryUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update time entry status and details."""
    entry = db.query(TimeEntry).filter(
        TimeEntry.id == entry_id,
        TimeEntry.user_id == current_user.id,
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Update fields
    for field, value in entry_update.dict(exclude_unset=True).items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    
    return TimeEntryResponse.from_orm(entry)
```

## Complete Integration Example

Here's a complete endpoint implementation:

```python
# app/api/v1/routes/time_entries.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse
from app.services.tasks.ingest import ingest_events_task

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.post("/ingest")
async def ingest_activity_signals(
    request: dict,
    current_user = Depends(get_current_user),
):
    """
    Ingest raw activity signals and generate suggested time entries.
    
    Queue async processing of activity signals into time entries.
    Returns task ID for status polling.
    """
    activity_signals = request.get("activity_signals", [])
    idle_threshold = request.get("idle_threshold_minutes", 5)
    max_merge_idle = request.get("max_merge_idle_minutes", 10)
    
    # Queue background task
    result = ingest_events_task.delay(
        user_id=current_user.id,
        activity_signals=activity_signals,
    )
    
    return {
        "status": "processing",
        "task_id": result.id,
        "message": "Activity signals queued for processing",
    }


@router.get("/ingest/{task_id}")
async def get_ingest_status(
    task_id: str,
    current_user = Depends(get_current_user),
):
    """Get status of activity signal ingestion task."""
    result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": result.status,
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.info)
    
    return response


@router.get("/pending-review")
async def list_pending_entries(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get time entries pending manual review."""
    query = db.query(TimeEntry).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.status == "pending",
    )
    
    total = query.count()
    entries = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "entries": [TimeEntryResponse.from_orm(e) for e in entries],
    }


@router.patch("/{entry_id}")
async def update_time_entry(
    entry_id: str,
    entry_update: TimeEntryUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update time entry status, project, and other details."""
    entry = db.query(TimeEntry).filter(
        TimeEntry.id == entry_id,
        TimeEntry.user_id == current_user.id,
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Update fields that were provided
    update_data = entry_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    
    return TimeEntryResponse.from_orm(entry)


@router.get("/")
async def list_time_entries(
    skip: int = 0,
    limit: int = 10,
    status: str | None = None,
    source: str | None = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List time entries with optional filtering."""
    query = db.query(TimeEntry).filter(
        TimeEntry.user_id == current_user.id,
    )
    
    if status:
        query = query.filter(TimeEntry.status == status)
    
    if source:
        query = query.filter(TimeEntry.source == source)
    
    total = query.count()
    entries = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "entries": [TimeEntryResponse.from_orm(e) for e in entries],
    }
```

## Usage Example

### 1. Client Submits Activity Signals

```bash
curl -X POST http://localhost:8000/api/v1/time-entries/ingest \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_signals": [
      {
        "timestamp": "2024-01-24T09:00:00Z",
        "app": "vscode",
        "type": "keyboard",
        "source_type": "keyboard"
      },
      {
        "timestamp": "2024-01-24T09:15:00Z",
        "app": "vscode",
        "type": "keyboard",
        "source_type": "keyboard"
      }
    ]
  }'
```

**Response:**
```json
{
  "status": "processing",
  "task_id": "a1b2c3d4-e5f6-g7h8-i9j0",
  "message": "Activity signals queued for processing"
}
```

### 2. Client Polls for Task Status

```bash
curl http://localhost:8000/api/v1/time-entries/ingest/a1b2c3d4-e5f6-g7h8-i9j0 \
  -H "Authorization: Bearer TOKEN"
```

**Response (Processing):**
```json
{
  "task_id": "a1b2c3d4-e5f6-g7h8-i9j0",
  "status": "PENDING"
}
```

**Response (Complete):**
```json
{
  "task_id": "a1b2c3d4-e5f6-g7h8-i9j0",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "suggested_count": 2,
    "created_count": 2,
    "created_ids": ["entry-1", "entry-2"],
    "verification_required": []
  }
}
```

### 3. Client Reviews Pending Entries

```bash
curl http://localhost:8000/api/v1/time-entries/pending-review \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "total": 2,
  "entries": [
    {
      "id": "entry-1",
      "started_at": "2024-01-24T09:00:00Z",
      "ended_at": "2024-01-24T09:15:00Z",
      "duration_minutes": 15,
      "status": "pending",
      "source": "auto",
      "activity_type": "focused_work"
    }
  ]
}
```

### 4. Client Approves Entry

```bash
curl -X PATCH http://localhost:8000/api/v1/time-entries/entry-1 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "project_id": "proj-123",
    "client_id": "client-456"
  }'
```

**Response:**
```json
{
  "id": "entry-1",
  "status": "approved",
  "started_at": "2024-01-24T09:00:00Z",
  "ended_at": "2024-01-24T09:15:00Z",
  "duration_minutes": 15,
  "project_id": "proj-123",
  "client_id": "client-456"
}
```

## Workflow Overview

```
User Activity (Keyboard, Mouse, App)
          ↓
Integration Captures Signals
          ↓
Client POST /ingest (Activity Signals)
          ↓
Server Queues Celery Task
          ↓
Task Processes Signals (Idle Detection → Classification → Heuristics)
          ↓
Task Creates Pending TimeEntry Records
          ↓
Client Polls GET /ingest/{task_id}
          ↓
Client Retrieves GET /pending-review
          ↓
User Reviews and Approves Entries
          ↓
Client PATCH /{entry_id} (status=approved)
          ↓
TimeEntry Marked as Approved (Ready for Billing)
```

## Configuration

Add to `app/config/settings.py`:

```python
# Time-Capture Configuration
IDLE_THRESHOLD_MINUTES = 5
MAX_MERGE_IDLE_MINUTES = 10
CONFIDENCE_VERIFY_THRESHOLD = 0.5

# Celery Configuration
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# Task Routing
CELERY_TASK_ROUTES = {
    "tasks.ingest_events": {"queue": "time_capture"},
    "tasks.generate_billing": {"queue": "billing"},
}

# Task Configuration
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour
CELERY_TASK_SOFT_TIME_LIMIT = 3000  # 50 minutes
```

## Error Handling

The system handles various error scenarios:

**Invalid User:**
```json
{
  "status": "error",
  "message": "User not found",
  "suggested_count": 0,
  "created_count": 0,
  "created_ids": [],
  "verification_required": []
}
```

**Invalid Signals:**
```json
{
  "status": "partial_success",
  "suggested_count": 2,
  "created_count": 1,
  "created_ids": ["entry-1"],
  "verification_required": [
    {
      "confidence": 0.3,
      "reason": "Signal timestamp missing",
      "description": "Signal #2 missing timestamp field"
    }
  ]
}
```

**Database Errors:**
- Automatic retry with exponential backoff
- Max 3 attempts
- Admin notification on final failure
