# Testing Guide

## Overview

BillOps backend includes comprehensive unit and integration tests using **pytest**. This guide covers setup, running tests, and best practices.

## Installation

All testing dependencies are included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key testing packages:
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage reporting
- **pytest-xdist** - Parallel test execution
- **pytest-timeout** - Test timeout management
- **pytest-mock** - Mocking utilities
- **httpx-mock** - HTTP mocking
- **factory-boy** - Test data factories

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration & fixtures
├── unit/                    # Unit tests
│   ├── test_models.py      # Model tests
│   ├── test_services.py    # Service tests
│   └── test_api_endpoints.py  # Endpoint tests
├── integration/            # Integration tests
│   ├── test_invoice_workflow.py  # Invoice workflows
│   ├── test_time_capture_workflow.py  # Time capture workflows
│   └── test_*.py           # Other integration tests
└── e2e/                    # End-to-end tests
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Unit + Integration (exclude E2E)
pytest -m "not e2e"

# Only slow tests
pytest -m slow
```

### Run Specific Test Files

```bash
# Single file
pytest tests/unit/test_models.py

# Multiple files
pytest tests/unit/test_models.py tests/unit/test_services.py

# Specific test class
pytest tests/unit/test_models.py::TestUserModel

# Specific test function
pytest tests/unit/test_models.py::TestUserModel::test_user_creation
```

### Run with Parallel Execution

```bash
# Run tests in 4 parallel workers
pytest -n 4

# Auto-detect number of CPUs
pytest -n auto
```

### Run with Coverage Report

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# Coverage with specific format
pytest --cov=app --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

### Run with Verbose Output

```bash
# Verbose mode (default in pytest.ini)
pytest -v

# Very verbose with full diffs
pytest -vv

# Show print statements
pytest -s

# Combine options
pytest -vvs --tb=long
```

### Run with Filtering

```bash
# Run tests matching pattern
pytest -k "invoice" # Runs all tests with "invoice" in name

# Run tests NOT matching pattern
pytest -k "not slow"

# Multiple patterns
pytest -k "invoice and not overdue"
```

## Fixtures

### Database Fixtures

#### `db: Session`
Fresh database session for each test, automatically rolled back.

```python
def test_user_creation(db: Session):
    user = User(email="test@example.com", ...)
    db.add(user)
    db.commit()
    assert user.id is not None
```

#### `client: TestClient`
FastAPI test client with test database injected.

```python
def test_api_endpoint(client: TestClient):
    response = client.get("/api/v1/users")
    assert response.status_code == 200
```

### Model Factory Fixtures

#### `test_user: User`
Pre-created test user with default data.

```python
def test_something(test_user: User):
    assert test_user.email == "test@example.com"
```

#### `test_client: Client`
Pre-created test client linked to `test_user`.

#### `test_project: Project`
Pre-created test project linked to `test_user` and `test_client`.

#### `test_time_entry: TimeEntry`
Pre-created test time entry.

#### `test_invoice: Invoice`
Pre-created test invoice.

#### `test_billing_rule: BillingRule`
Pre-created test billing rule.

#### `test_payment: Payment`
Pre-created test payment linked to `test_invoice`.

### Factory Functions

#### `make_time_entry_factory`
Factory for creating multiple time entries with custom parameters.

```python
def test_multiple_entries(make_time_entry_factory):
    entry1 = make_time_entry_factory(duration_minutes=60)
    entry2 = make_time_entry_factory(duration_minutes=120)
    assert entry1.duration_minutes == 60
    assert entry2.duration_minutes == 120
```

#### `make_invoice_factory`
Factory for creating multiple invoices.

```python
def test_invoices(make_invoice_factory):
    inv1 = make_invoice_factory(status="draft")
    inv2 = make_invoice_factory(status="sent")
```

### Utility Fixtures

#### `auth_headers: dict`
Authorization headers with valid JWT token for authenticated requests.

```python
def test_protected_endpoint(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 200
```

#### `utc_now: datetime`
Current UTC datetime.

```python
def test_with_time(utc_now: datetime):
    assert utc_now.tzinfo == timezone.utc
```

## Test Markers

Custom markers for organizing tests:

```python
# Unit test
@pytest.mark.unit
def test_something():
    pass

# Integration test
@pytest.mark.integration
def test_workflow():
    pass

# Requires database
@pytest.mark.db
def test_database():
    pass

# Slow test (takes >1 second)
@pytest.mark.slow
def test_slow_operation():
    pass
```

Run by marker:

```bash
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "db"          # Only tests using database
pytest -m "not slow"    # Skip slow tests
```

## Writing Tests

### Unit Test Template

```python
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.user import UserService

@pytest.mark.unit
@pytest.mark.db
class TestUserService:
    """Tests for UserService."""

    def test_create_user(self, db: Session):
        """Test creating a user."""
        service = UserService(db)
        user = service.create(
            email="new@example.com",
            first_name="New",
            last_name="User",
        )
        assert user.id is not None
        assert user.email == "new@example.com"

    def test_get_user_by_id(self, db: Session, test_user: User):
        """Test retrieving user by ID."""
        service = UserService(db)
        retrieved = service.get_by_id(test_user.id)
        assert retrieved.id == test_user.id
```

### Integration Test Template

```python
@pytest.mark.integration
@pytest.mark.db
class TestInvoiceWorkflow:
    """Integration tests for invoice generation."""

    def test_complete_workflow(
        self,
        db: Session,
        test_user,
        test_project,
        make_time_entry_factory,
    ):
        """Test complete invoice generation workflow."""
        # Setup
        for i in range(5):
            make_time_entry_factory(duration_minutes=120)

        # Execute
        service = InvoiceService(db)
        invoice = service.create(...)

        # Assert
        assert invoice.total_cents > 0
```

### API Endpoint Test Template

```python
@pytest.mark.unit
class TestInvoiceEndpoints:
    """Tests for invoice API endpoints."""

    def test_list_invoices(self, client: TestClient, auth_headers: dict):
        """Test listing invoices."""
        response = client.get(
            "/api/v1/invoices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
```

## Best Practices

### 1. **Test Independence**
Each test should be independent and not rely on test execution order.

```python
# ❌ Bad
def test_create_user():
    user = User(...)
    db.add(user)
    db.commit()

def test_get_user():  # Relies on previous test
    user = db.query(User).first()
    assert user is not None

# ✅ Good
def test_create_user(db: Session):
    user = User(...)
    db.add(user)
    db.commit()
    assert user.id is not None

def test_get_user(db: Session, test_user: User):
    assert test_user is not None
```

### 2. **Clear Test Names**
Test names should describe what's being tested.

```python
# ❌ Bad
def test_it_works():
    pass

# ✅ Good
def test_invoice_status_transitions_from_draft_to_sent():
    pass
```

### 3. **Arrange-Act-Assert Pattern**
Organize tests with clear setup, execution, and assertion phases.

```python
def test_calculate_invoice_total(db: Session, test_invoice: Invoice):
    # Arrange
    line_item = InvoiceLineItem(
        invoice_id=test_invoice.id,
        amount_cents=100000,
    )
    db.add(line_item)
    db.commit()

    # Act
    service = InvoiceService(db)
    total = service.calculate_total(test_invoice.id)

    # Assert
    assert total == 100000
```

### 4. **Use Fixtures Over Setup Methods**
Prefer pytest fixtures to setUp/tearDown methods.

```python
# ❌ Bad
class TestUser:
    def setup_method(self):
        self.db = create_test_db()
    
    def teardown_method(self):
        self.db.close()

# ✅ Good
def test_user(db: Session):
    pass
```

### 5. **Mock External Services**
Mock API calls and external dependencies.

```python
def test_send_email(mocker):
    mock_email = mocker.patch("app.services.email.send_email")
    # Test code...
    mock_email.assert_called_once()
```

### 6. **Test Edge Cases**
Include tests for boundary conditions and error cases.

```python
def test_invoice_with_zero_amount(db: Session):
    """Test invoice with zero amount."""
    invoice = Invoice(total_cents=0, ...)
    db.add(invoice)
    db.commit()
    assert invoice.total_cents == 0

def test_time_entry_with_negative_duration_rejected():
    """Test that negative durations are rejected."""
    with pytest.raises(ValueError):
        TimeEntry(duration_minutes=-60, ...)
```

### 7. **Parametrize Tests**
Use parametrization to test multiple scenarios.

```python
@pytest.mark.parametrize("status", ["draft", "sent", "paid"])
def test_invoice_status_transitions(db: Session, test_invoice, status):
    """Test all valid invoice statuses."""
    test_invoice.status = status
    db.commit()
    assert test_invoice.status == status
```

### 8. **Test Both Success and Failure Paths**
Test what happens when things go wrong.

```python
def test_create_user_with_duplicate_email_fails(db: Session):
    """Test that duplicate emails are rejected."""
    User(email="test@example.com", ...)
    db.add(user)
    db.commit()

    with pytest.raises(IntegrityError):
        User(email="test@example.com", ...)
        db.add(user)
        db.commit()
```

## Coverage Goals

Target at least 80% code coverage:

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

Coverage by module:
- Models: 95%+
- Services: 90%+
- API Routes: 85%+
- Utilities: 90%+

## Continuous Integration

Tests are run automatically on GitHub Actions. To run locally:

```bash
# Unit tests
pytest -m unit --cov=app

# Integration tests
pytest -m integration

# All tests with coverage
pytest --cov=app --cov-report=term-missing
```

## Debugging Tests

### Print Debugging
Use `-s` flag to see print statements:

```bash
pytest -s tests/unit/test_models.py::TestUserModel::test_user_creation
```

### Drop into Debugger
Use `pytest.set_trace()`:

```python
def test_something(db: Session):
    import pytest
    pytest.set_trace()
    # Debugger will break here
```

Or use pytest's `--pdb` flag:

```bash
pytest --pdb tests/unit/test_models.py
```

### Show Local Variables on Failure
Use `--showlocals`:

```bash
pytest --showlocals tests/unit/test_models.py
```

## Tips & Tricks

### Run Failing Tests First
```bash
pytest --lf
```

### Run Last N Tests
```bash
pytest --last-failed --maxfail=3
```

### Exit on First Failure
```bash
pytest -x
```

### Repeat Last Failed Test
```bash
pytest -lf
```

### Profile Slow Tests
```bash
pytest --durations=10
```

## Troubleshooting

### Database Locking Issues
If you see "database is locked" errors:
- Ensure transactions are properly rolled back
- Check that test database isn't being used by other processes
- Clear SQLite lock files: `rm *.db-wal`

### Import Errors
Ensure app is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Fixture Not Found
Ensure fixtures are defined in `conftest.py` at the correct scope:
- `function` scope (default) - fresh for each test
- `session` scope - shared across all tests

## Performance

### Run Tests in Parallel
```bash
# Use 4 workers
pytest -n 4

# Auto-detect CPU cores
pytest -n auto
```

### Skip Slow Tests
```bash
pytest -m "not slow"
```

### Filter Tests
```bash
# Run specific tests faster
pytest tests/unit/test_models.py -k user
```

## Resources

- **Pytest Docs**: https://docs.pytest.org/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/20/faq/testing.html
- **FastAPI Testing**: https://fastapi.tiangolo.com/advanced/testing-databases/
