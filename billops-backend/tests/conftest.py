"""
Pytest configuration and fixtures for BillOps tests.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.project import Project
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.models.billing_rule import BillingRule
from app.models.payment import Payment
from app.core.hashing import hash_password


# Use in-memory SQLite for tests (or PostgreSQL test database)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def SessionLocal(engine):
    """Create session factory for tests."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db(SessionLocal) -> Generator[Session, None, None]:
    """
    Database session fixture for each test.
    
    Yields a fresh session for each test and rolls back after.
    """
    connection = SessionLocal.kw["bind"].connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.rollback()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> TestClient:
    """
    Test client fixture that uses test database.
    """

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ============================================================================
# Factory Fixtures - Create test data
# ============================================================================


@pytest.fixture
def test_user_data() -> dict:
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_verified": True,
    }


@pytest.fixture
def test_user(db: Session, test_user_data: dict) -> User:
    """Create a test user."""
    user_data = test_user_data.copy()
    password = user_data.pop("password")

    user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        hashed_password=hash_password(password),
        is_active=user_data.get("is_active", True),
        is_verified=user_data.get("is_verified", True),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_client_data() -> dict:
    """Test client data."""
    return {
        "name": "Acme Corporation",
        "email": "billing@acme.com",
        "phone": "+1-555-0123",
        "currency": "USD",
        "tax_id": "12-3456789",
    }


@pytest.fixture
def test_client(db: Session, test_user: User, test_client_data: dict) -> Client:
    """Create a test client."""
    client = Client(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name=test_client_data["name"],
        email=test_client_data["email"],
        phone=test_client_data.get("phone"),
        currency=test_client_data.get("currency", "USD"),
        tax_id=test_client_data.get("tax_id"),
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture
def test_project(db: Session, test_user: User, test_client: Client) -> Project:
    """Create a test project."""
    project = Project(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=test_client.id,
        name="Test Project",
        description="A test project",
        hourly_rate_cents=15000,  # $150.00
        currency="USD",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_time_entry(db: Session, test_user: User, test_project: Project) -> TimeEntry:
    """Create a test time entry."""
    start_time = datetime.now(timezone.utc) - timedelta(hours=1)
    end_time = datetime.now(timezone.utc)

    time_entry = TimeEntry(
        id=uuid.uuid4(),
        user_id=test_user.id,
        project_id=test_project.id,
        description="Test work session",
        start_time=start_time,
        end_time=end_time,
        duration_minutes=60,
        is_billable=True,
        is_billed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(time_entry)
    db.commit()
    db.refresh(time_entry)
    return time_entry


@pytest.fixture
def test_billing_rule(db: Session, test_user: User, test_client: Client) -> BillingRule:
    """Create a test billing rule."""
    rule = BillingRule(
        id=uuid.uuid4(),
        user_id=test_user.id,
        client_id=test_client.id,
        name="Standard Billing",
        billable_hours_per_month=160,
        base_rate_cents=150000,  # $1500.00
        overtime_rate_cents=225000,  # $2250.00
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@pytest.fixture
def test_invoice(
    db: Session,
    test_client: Client,
    test_project: Project,
) -> Invoice:
    """Create a test invoice."""
    invoice = Invoice(
        id=uuid.uuid4(),
        client_id=test_client.id,
        project_id=test_project.id,
        invoice_number=f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001",
        currency="USD",
        status="draft",
        issue_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=30),
        subtotal_cents=150000,  # $1500.00
        tax_cents=0,
        total_cents=150000,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@pytest.fixture
def test_invoice_line_item(db: Session, test_invoice: Invoice) -> InvoiceLineItem:
    """Create a test invoice line item."""
    line_item = InvoiceLineItem(
        id=uuid.uuid4(),
        invoice_id=test_invoice.id,
        description="Professional services - 10 hours @ $150/hr",
        quantity=10,
        rate_cents=150000,
        amount_cents=150000,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(line_item)
    db.commit()
    db.refresh(line_item)
    return line_item


@pytest.fixture
def test_payment(
    db: Session,
    test_invoice: Invoice,
) -> Payment:
    """Create a test payment."""
    payment = Payment(
        id=uuid.uuid4(),
        invoice_id=test_invoice.id,
        amount_cents=150000,
        payment_date=datetime.now(timezone.utc),
        payment_method="bank_transfer",
        status="completed",
        transaction_id="TXN-123456",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def auth_headers(client: TestClient, test_user_data: dict) -> dict:
    """
    Get authorization headers for authenticated requests.
    
    Returns a dict with Authorization header containing JWT token.
    """
    # Register user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "first_name": test_user_data["first_name"],
            "last_name": test_user_data["last_name"],
        },
    )

    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def utc_now():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def make_time_entry_factory(db: Session, test_user: User, test_project: Project):
    """Factory for creating multiple time entries."""

    def _make_time_entry(
        start_time=None,
        duration_minutes=60,
        description="Work",
        is_billable=True,
    ) -> TimeEntry:
        if start_time is None:
            start_time = datetime.now(timezone.utc) - timedelta(hours=1)

        end_time = start_time + timedelta(minutes=duration_minutes)

        time_entry = TimeEntry(
            id=uuid.uuid4(),
            user_id=test_user.id,
            project_id=test_project.id,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            is_billable=is_billable,
            is_billed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(time_entry)
        db.commit()
        db.refresh(time_entry)
        return time_entry

    return _make_time_entry


@pytest.fixture
def make_invoice_factory(db: Session, test_client: Client, test_project: Project):
    """Factory for creating multiple invoices."""

    def _make_invoice(
        invoice_number=None,
        status="draft",
        subtotal_cents=150000,
        issue_date=None,
    ) -> Invoice:
        if invoice_number is None:
            invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"

        if issue_date is None:
            issue_date = datetime.now(timezone.utc)

        invoice = Invoice(
            id=uuid.uuid4(),
            client_id=test_client.id,
            project_id=test_project.id,
            invoice_number=invoice_number,
            currency="USD",
            status=status,
            issue_date=issue_date,
            due_date=issue_date + timedelta(days=30),
            subtotal_cents=subtotal_cents,
            tax_cents=0,
            total_cents=subtotal_cents,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    return _make_invoice


# ============================================================================
# Markers for organizing tests
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "db: mark test as requiring database")
