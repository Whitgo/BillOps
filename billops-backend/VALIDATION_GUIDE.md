# Complete Testing & Validation Guide

## Overview

This guide covers all testing, validation, and quality assurance procedures for BillOps.

## Test Suite Structure

### Unit Tests (`tests/unit/`)
- **test_models.py** - Data model validation (10+ models, 50+ tests)
- **test_services.py** - Business logic validation (6+ services, 45+ tests)
- **test_api_endpoints.py** - API endpoint validation (35+ tests)

**Run**: `pytest tests/unit/ -v`

### Integration Tests (`tests/integration/`)
- **test_invoice_workflow.py** - Invoice generation workflows
- **test_time_capture_workflow.py** - Time capture workflows
- **test_notifications.py** - Email/Slack notifications
- **test_integrations.py** - Calendar/integration syncs

**Run**: `pytest tests/integration/ -v`

### End-to-End Tests (`tests/e2e/`)
- **test_workflows.py** - Complete business workflows
- **test_data_consistency.py** - Data integrity validation

**Run**: `pytest tests/e2e/ -v`

---

## Running Regression Tests

### Quick Start

Run the full regression testing suite:

```bash
cd billops-backend
python run_regression_tests.py
```

This runs:
1. All unit tests
2. All integration tests
3. All E2E tests
4. Code coverage analysis
5. Generates comprehensive report

### Individual Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# By marker
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m "not slow"    # Skip slow tests
```

### With Coverage

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# Coverage with missing line reporting
pytest tests/ --cov=app --cov-report=term-missing

# Fail if below threshold
pytest tests/ --cov=app --cov-fail-under=80
```

### In Parallel

```bash
# Use 4 workers
pytest tests/ -n 4

# Auto-detect CPU cores
pytest tests/ -n auto
```

---

## Invoice Generation Validation

### End-to-End Invoice Workflow

Validates complete flow: time entries → invoice generation → payment

**Test**: `test_complete_invoice_workflow_e2e`

**Steps**:
1. ✓ Create multiple time entries
2. ✓ Calculate billable hours
3. ✓ Generate invoice
4. ✓ Add line items
5. ✓ Verify amounts
6. ✓ Update status

**Run**:
```bash
pytest tests/e2e/test_workflows.py::TestInvoiceGenerationE2E::test_complete_invoice_workflow_e2e -v
```

### Invoice with Tax

Validates tax calculation and total computation.

**Test**: `test_invoice_with_tax_calculation`

### Invoice Status Workflow

Validates state transitions: draft → sent → paid → overdue

**Test**: `test_invoice_status_workflow`

### Payment Recording

Validates partial and full payment tracking.

**Test**: `test_invoice_payment_workflow_e2e`

---

## Time Capture Validation

### Time Entry Creation

Validates time tracking and duration calculation.

**Tests**:
- `test_time_entry_creation` - Basic creation
- `test_time_entry_duration_calculation` - Duration accuracy
- `test_time_entry_non_billable` - Non-billable flagging

### Daily Time Tracking

Validates daily work session aggregation.

**Test**: `test_daily_time_tracking_workflow`

**Checks**:
- ✓ Multiple sessions per day
- ✓ Total hours calculation
- ✓ Gap/overlap detection

### Multi-Project Tracking

Validates time split across multiple projects.

**Test**: `test_multi_project_time_tracking`

### Weekly/Monthly Summaries

**Tests**:
- `test_weekly_time_summary` - Week aggregation
- `test_monthly_time_tracking_with_overtime` - Monthly totals & overtime

### Billable vs Non-billable

Validates correct filtering of billable entries.

**Test**: `test_mixed_billable_nonbillable_time_entries`

---

## Integration Validation

### Calendar Integration

**Tests**:
- `test_calendar_integration_e2e` - Calendar sync
- `test_sync_google_calendar` - Google Calendar
- `test_sync_outlook_calendar` - Outlook Calendar

### Slack Integration

**Tests**:
- `test_slack_integration_e2e` - Slack status
- `test_sync_slack_status` - Status sync
- `test_send_slack_notifications` - Notifications

### Integration Health Checks

**Test**: `test_health_check_integrations`

Validates:
- ✓ API connectivity
- ✓ Token validity
- ✓ Rate limiting
- ✓ Failure recovery

---

## Authentication & Authorization

### Registration Flow

**Test**: `test_register_user`

Validates:
- ✓ Account creation
- ✓ Password hashing
- ✓ Email validation
- ✓ Duplicate prevention

### Login Flow

**Test**: `test_login` / `test_full_auth_flow`

Validates:
- ✓ Credential verification
- ✓ Token generation
- ✓ Token expiration

### Protected Endpoints

**Tests**: All endpoint tests with `auth_headers`

Validates:
- ✓ Unauthorized rejection
- ✓ Token validation
- ✓ User isolation

---

## Data Consistency Validation

### User Data Consistency

**Test**: `test_user_data_consistency`

### Client-Project Relationships

**Test**: `test_client_project_consistency`

### Invoice-Payment Reconciliation

**Test**: `test_invoice_line_items_sum_to_total`

### Time Entry Integrity

**Test**: `test_time_entry_data_integrity_across_operations`

---

## API Validation

### Endpoint Response Formats

All endpoints validated for:
- ✓ Correct status codes
- ✓ Valid JSON response
- ✓ Required fields present
- ✓ Field types correct

### Error Handling

**Tests**:
- `test_api_error_handling` - Invalid requests
- `test_missing_required_fields` - Validation
- `test_unauthorized_access` - Auth failures

### Pagination

**Test**: `test_list_pagination`

Validates:
- ✓ Skip/limit parameters
- ✓ Total count
- ✓ Cursor handling

### Filtering

**Tests**:
- `test_filter_invoices_by_status`
- `test_filter_time_entries_by_date`
- `test_filter_clients_by_active_status`

---

## Performance Validation

### Response Time

API calls tracked for performance:
- Target: < 200ms average
- Slow: > 1000ms logged as warning

**Check**:
```bash
pytest tests/ -v --durations=10
```

### Concurrent Operations

**Test**: `test_concurrent_time_entries_same_project`

Validates handling of simultaneous requests.

### Load Testing

For production:
```bash
# Install locust
pip install locust

# Create locustfile.py with test scenarios
# Run: locust -f locustfile.py --host=http://localhost:8000
```

---

## Code Quality Checks

### Static Analysis

```bash
# Lint with flake8
flake8 app tests

# Type checking with mypy
mypy app

# Security scan with bandit
bandit -r app
```

### Code Coverage

Target: **80%+ overall coverage**

By module:
- Models: 95%+
- Services: 90%+
- API Routes: 85%+
- Utils: 90%+

Check coverage:
```bash
pytest tests/ --cov=app --cov-report=html --cov-fail-under=80
```

---

## Analytics Validation

### Event Tracking

Validates analytics events are logged:

```python
from app.services.analytics import get_analytics, EventType

analytics = get_analytics()

# Track custom event
analytics.track_invoice_event(
    EventType.INVOICE_CREATED,
    invoice_id="123",
    user_id="456",
)
```

### Metrics Collection

```python
from app.services.analytics import get_metrics

metrics = get_metrics()
metrics.increment_counter("invoices_generated")
metrics.set_gauge("active_users", 42)
metrics.record_histogram("invoice_generation_time_ms", 125.5)
```

### Log Verification

Check logs for analytics events:

```bash
# View recent analytics logs
tail -f logs/app.log | grep "EVENT:"

# Search for specific events
grep "invoice.created" logs/app.log
```

---

## API Documentation Validation

### OpenAPI Schema

Access and validate OpenAPI spec:

```bash
# Download schema
curl http://localhost:8000/api/openapi.json > openapi.json

# Validate schema
openapi-generator-cli validate -i openapi.json
```

### Swagger UI

Interactive documentation:
```
http://localhost:8000/api/docs
```

Validate:
- ✓ All endpoints listed
- ✓ Request/response schemas correct
- ✓ Required fields marked
- ✓ Authentication shown

### ReDoc

Alternative documentation:
```
http://localhost:8000/api/redoc
```

---

## Pre-Production Checklist

### Before Release

- [ ] All tests passing (100% required)
- [ ] Coverage above 80%
- [ ] No linting errors
- [ ] No security vulnerabilities
- [ ] Performance benchmarks met
- [ ] API documentation complete
- [ ] Analytics instrumented
- [ ] Error handling tested
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Environment variables documented
- [ ] Database migrations reviewed
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] Monitoring alerts set up

---

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Commits to main
- Scheduled daily runs

### Local Pre-commit

Set up pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml with:
# - pytest
# - flake8
# - mypy
# - black

pre-commit install
```

---

## Troubleshooting

### Test Failures

**Database locked**:
```bash
rm *.db-wal
pytest tests/
```

**Import errors**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

**Fixture not found**:
- Ensure fixtures in conftest.py
- Check fixture scope (function/session)

### Slow Tests

Profile slow tests:
```bash
pytest tests/ --durations=10
```

Skip slow tests:
```bash
pytest -m "not slow"
```

### Coverage Issues

Generate detailed coverage:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Resources

- **Pytest**: https://docs.pytest.org/
- **OpenAPI**: https://spec.openapis.org/
- **FastAPI Testing**: https://fastapi.tiangolo.com/advanced/testing-databases/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/20/faq/testing.html

---

## Contact

For testing support:
- Create issue on GitHub
- Email: testing@billops.com
- Slack: #testing channel
