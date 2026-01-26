"""
Unit tests for API endpoints.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.models.invoice import Invoice


@pytest.mark.unit
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_register_user(self, client: TestClient, test_user_data: dict):
        """Test user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 201
        assert response.json()["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate email."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
                "first_name": test_user_data["first_name"],
                "last_name": test_user_data["last_name"],
            },
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user_data["email"],
                "password": "DifferentPass123!",
                "first_name": "Other",
                "last_name": "User",
            },
        )
        assert response.status_code == 400

    def test_login(self, client: TestClient, test_user_data: dict):
        """Test user login."""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
                "first_name": test_user_data["first_name"],
                "last_name": test_user_data["last_name"],
            },
        )

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestClientEndpoints:
    """Tests for client endpoints."""

    def test_create_client(self, client: TestClient, auth_headers: dict):
        """Test creating a client."""
        response = client.post(
            "/api/v1/clients",
            json={
                "name": "Test Corporation",
                "email": "test@corp.com",
                "currency": "USD",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Test Corporation"

    def test_get_client(self, client: TestClient, auth_headers: dict, test_client):
        """Test retrieving a client."""
        response = client.get(
            f"/api/v1/clients/{test_client.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_client.id)

    def test_list_clients(self, client: TestClient, auth_headers: dict, test_client):
        """Test listing clients."""
        response = client.get(
            "/api/v1/clients",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data

    def test_update_client(self, client: TestClient, auth_headers: dict, test_client):
        """Test updating a client."""
        response = client.patch(
            f"/api/v1/clients/{test_client.id}",
            json={"name": "Updated Corp"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Corp"

    def test_delete_client(self, client: TestClient, auth_headers: dict, test_client):
        """Test deleting a client."""
        response = client.delete(
            f"/api/v1/clients/{test_client.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204 or response.status_code == 200

    def test_create_client_missing_auth(self, client: TestClient):
        """Test creating client without authentication."""
        response = client.post(
            "/api/v1/clients",
            json={
                "name": "Test Corporation",
                "email": "test@corp.com",
            },
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestProjectEndpoints:
    """Tests for project endpoints."""

    def test_create_project(self, client: TestClient, auth_headers: dict, test_client):
        """Test creating a project."""
        response = client.post(
            "/api/v1/projects",
            json={
                "client_id": str(test_client.id),
                "name": "New Project",
                "hourly_rate_cents": 15000,
                "currency": "USD",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["name"] == "New Project"

    def test_get_project(self, client: TestClient, auth_headers: dict, test_project):
        """Test retrieving a project."""
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_project.id)

    def test_list_projects(self, client: TestClient, auth_headers: dict, test_project):
        """Test listing projects."""
        response = client.get(
            "/api/v1/projects",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_project(self, client: TestClient, auth_headers: dict, test_project):
        """Test updating a project."""
        response = client.patch(
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Updated Project"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Project"


@pytest.mark.unit
class TestTimeEntryEndpoints:
    """Tests for time entry endpoints."""

    def test_create_time_entry(self, client: TestClient, auth_headers: dict, test_project):
        """Test creating a time entry."""
        now = datetime.now(timezone.utc)
        response = client.post(
            "/api/v1/time-entries",
            json={
                "project_id": str(test_project.id),
                "description": "Work session",
                "start_time": (now - timedelta(hours=1)).isoformat(),
                "end_time": now.isoformat(),
                "is_billable": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["description"] == "Work session"

    def test_get_time_entry(self, client: TestClient, auth_headers: dict, test_time_entry):
        """Test retrieving a time entry."""
        response = client.get(
            f"/api/v1/time-entries/{test_time_entry.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_time_entry.id)

    def test_list_time_entries(self, client: TestClient, auth_headers: dict, test_time_entry):
        """Test listing time entries."""
        response = client.get(
            "/api/v1/time-entries",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_time_entries_by_date(self, client: TestClient, auth_headers: dict, test_time_entry):
        """Test listing time entries by date range."""
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=1)).date().isoformat()
        end_date = (now + timedelta(days=1)).date().isoformat()

        response = client.get(
            f"/api/v1/time-entries?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_time_entry(self, client: TestClient, auth_headers: dict, test_time_entry):
        """Test updating a time entry."""
        response = client.patch(
            f"/api/v1/time-entries/{test_time_entry.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_delete_time_entry(self, client: TestClient, auth_headers: dict, test_time_entry):
        """Test deleting a time entry."""
        response = client.delete(
            f"/api/v1/time-entries/{test_time_entry.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204 or response.status_code == 200


@pytest.mark.unit
class TestInvoiceEndpoints:
    """Tests for invoice endpoints."""

    def test_get_invoice(self, client: TestClient, auth_headers: dict, test_invoice: Invoice):
        """Test retrieving an invoice."""
        response = client.get(
            f"/api/v1/invoices/{test_invoice.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_invoice.id)

    def test_list_invoices(self, client: TestClient, auth_headers: dict, test_invoice: Invoice):
        """Test listing invoices."""
        response = client.get(
            "/api/v1/invoices",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_invoices_by_status(self, client: TestClient, auth_headers: dict, test_invoice: Invoice):
        """Test listing invoices by status."""
        response = client.get(
            "/api/v1/invoices?status=draft",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_list_invoices_by_client(self, client: TestClient, auth_headers: dict, test_invoice: Invoice):
        """Test listing invoices by client."""
        response = client.get(
            f"/api/v1/invoices?client_id={test_invoice.client_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_invoice_status(self, client: TestClient, auth_headers: dict, test_invoice: Invoice):
        """Test updating invoice status."""
        response = client.patch(
            f"/api/v1/invoices/{test_invoice.id}",
            json={"status": "sent"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "sent"

    def test_download_invoice_pdf(self, client: TestClient, auth_headers: dict, test_invoice: Invoice, test_invoice_line_item):
        """Test downloading invoice as PDF."""
        response = client.get(
            f"/api/v1/invoices/{test_invoice.id}/pdf",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")


@pytest.mark.unit
class TestBillingRuleEndpoints:
    """Tests for billing rule endpoints."""

    def test_create_billing_rule(self, client: TestClient, auth_headers: dict, test_client):
        """Test creating a billing rule."""
        response = client.post(
            "/api/v1/billing-rules",
            json={
                "client_id": str(test_client.id),
                "name": "Standard Rate",
                "billable_hours_per_month": 160,
                "base_rate_cents": 150000,
                "overtime_rate_cents": 225000,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Standard Rate"

    def test_get_billing_rule(self, client: TestClient, auth_headers: dict, test_billing_rule):
        """Test retrieving a billing rule."""
        response = client.get(
            f"/api/v1/billing-rules/{test_billing_rule.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_billing_rule.id)

    def test_list_billing_rules(self, client: TestClient, auth_headers: dict, test_billing_rule):
        """Test listing billing rules."""
        response = client.get(
            "/api/v1/billing-rules",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_billing_rule(self, client: TestClient, auth_headers: dict, test_billing_rule):
        """Test updating a billing rule."""
        response = client.patch(
            f"/api/v1/billing-rules/{test_billing_rule.id}",
            json={"base_rate_cents": 200000},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["base_rate_cents"] == 200000


@pytest.mark.unit
class TestPaymentEndpoints:
    """Tests for payment endpoints."""

    def test_create_payment(self, client: TestClient, auth_headers: dict, test_invoice: Invoice):
        """Test recording a payment."""
        response = client.post(
            f"/api/v1/invoices/{test_invoice.id}/payments",
            json={
                "amount_cents": 150000,
                "payment_method": "bank_transfer",
                "transaction_id": "TXN-12345",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_list_payments(self, client: TestClient, auth_headers: dict, test_invoice: Invoice, test_payment):
        """Test listing payments for invoice."""
        response = client.get(
            f"/api/v1/invoices/{test_invoice.id}/payments",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_payment(self, client: TestClient, auth_headers: dict, test_invoice: Invoice, test_payment):
        """Test retrieving a payment."""
        response = client.get(
            f"/api/v1/invoices/{test_invoice.id}/payments/{test_payment.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.unit
class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
