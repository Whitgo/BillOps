# BillOps API Documentation

## Overview

BillOps is a comprehensive REST API for automated billing and time capture. This document provides detailed information about all available endpoints.

**Base URL**: `https://api.billops.com/api/v1` (Production)  
**Development URL**: `http://localhost:8000/api/v1`

## Authentication

All protected endpoints require JWT authentication via the `Authorization` header:

```bash
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token

**Endpoint**: `POST /auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

## Core Concepts

### Users
Represents a user of the BillOps platform. Users manage clients, projects, and time entries.

### Clients
Represent organizations that you bill. Each client has a billing rate and settings.

### Projects
Represent work assignments for clients. Time entries are tracked against projects.

### Time Entries
Records of work performed, associated with a project and user.

### Invoices
Generated from billable time entries, sent to clients for payment.

### Payments
Records of payments received against invoices.

### Billing Rules
Configure rates and billing terms for clients.

### Integrations
Connect external services like Google Calendar and Slack.

---

## Endpoint Reference

### Authentication (`/auth`)

#### Register User
Create a new BillOps account.

**Endpoint**: `POST /auth/register`

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true
}
```

#### Login
Authenticate and get JWT token.

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### Users (`/users`)

#### Get Current User
Get profile of authenticated user.

**Endpoint**: `GET /users/me`

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <token>"
```

**Response**: `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Update Profile
Update user information.

**Endpoint**: `PATCH /users/me`

**Request**:
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

---

### Clients (`/clients`)

#### List Clients
Get all clients for authenticated user.

**Endpoint**: `GET /clients`

**Query Parameters**:
- `skip` (int): Number of items to skip (default: 0)
- `limit` (int): Maximum items to return (default: 50)
- `is_active` (bool): Filter by active status

```bash
curl "http://localhost:8000/api/v1/clients?limit=10" \
  -H "Authorization: Bearer <token>"
```

**Response**: `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Acme Corporation",
    "email": "billing@acme.com",
    "phone": "+1-555-0123",
    "currency": "USD",
    "tax_id": "12-3456789",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

#### Create Client
Create a new client.

**Endpoint**: `POST /clients`

**Request**:
```json
{
  "name": "Tech Startup Inc",
  "email": "billing@techstartup.com",
  "currency": "USD",
  "phone": "+1-555-0456",
  "tax_id": "98-7654321"
}
```

**Response**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Tech Startup Inc",
  "email": "billing@techstartup.com",
  "currency": "USD",
  "is_active": true
}
```

#### Get Client
Get details of a specific client.

**Endpoint**: `GET /clients/{client_id}`

```bash
curl http://localhost:8000/api/v1/clients/550e8400-e29b-41d4-a716-446655440001 \
  -H "Authorization: Bearer <token>"
```

#### Update Client
Update client information.

**Endpoint**: `PATCH /clients/{client_id}`

**Request**:
```json
{
  "name": "Updated Client Name",
  "phone": "+1-555-0789"
}
```

#### Delete Client
Deactivate a client.

**Endpoint**: `DELETE /clients/{client_id}`

**Response**: `204 No Content`

---

### Projects (`/projects`)

#### List Projects
Get all projects.

**Endpoint**: `GET /projects`

**Query Parameters**:
- `client_id` (string): Filter by client
- `is_active` (bool): Filter by status

```bash
curl "http://localhost:8000/api/v1/projects?client_id=550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer <token>"
```

#### Create Project
Create a new project.

**Endpoint**: `POST /projects`

**Request**:
```json
{
  "client_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Website Redesign",
  "description": "Complete website overhaul",
  "hourly_rate_cents": 15000,
  "currency": "USD"
}
```

**Response**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "client_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Website Redesign",
  "hourly_rate_cents": 15000,
  "currency": "USD",
  "is_active": true
}
```

#### Get Project
Get project details.

**Endpoint**: `GET /projects/{project_id}`

#### Update Project
Update project information.

**Endpoint**: `PATCH /projects/{project_id}`

---

### Time Entries (`/time-entries`)

#### List Time Entries
Get time entries with optional filtering.

**Endpoint**: `GET /time-entries`

**Query Parameters**:
- `start_date` (date): Start of date range (YYYY-MM-DD)
- `end_date` (date): End of date range
- `project_id` (string): Filter by project
- `is_billable` (bool): Filter by billable status

```bash
curl "http://localhost:8000/api/v1/time-entries?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response**: `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440020",
    "project_id": "550e8400-e29b-41d4-a716-446655440010",
    "description": "Development work",
    "start_time": "2024-01-15T09:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "duration_minutes": 90,
    "is_billable": true,
    "is_billed": false,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

#### Create Time Entry
Log a time entry.

**Endpoint**: `POST /time-entries`

**Request**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440010",
  "description": "Development and testing",
  "start_time": "2024-01-15T09:00:00Z",
  "end_time": "2024-01-15T12:00:00Z",
  "is_billable": true
}
```

**Response**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440021",
  "project_id": "550e8400-e29b-41d4-a716-446655440010",
  "description": "Development and testing",
  "duration_minutes": 180,
  "is_billable": true,
  "is_billed": false
}
```

#### Get Time Entry
Get details of a specific time entry.

**Endpoint**: `GET /time-entries/{entry_id}`

#### Update Time Entry
Update time entry details.

**Endpoint**: `PATCH /time-entries/{entry_id}`

#### Delete Time Entry
Delete a time entry.

**Endpoint**: `DELETE /time-entries/{entry_id}`

---

### Invoices (`/invoices`)

#### List Invoices
Get all invoices.

**Endpoint**: `GET /invoices`

**Query Parameters**:
- `status` (string): Filter by status (draft, sent, paid, overdue, canceled)
- `client_id` (string): Filter by client
- `start_date` (date): Filter by date range

```bash
curl "http://localhost:8000/api/v1/invoices?status=draft" \
  -H "Authorization: Bearer <token>"
```

**Response**: `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "client_id": "550e8400-e29b-41d4-a716-446655440001",
    "invoice_number": "INV-2024-001",
    "status": "draft",
    "issue_date": "2024-01-15T00:00:00Z",
    "due_date": "2024-02-15T00:00:00Z",
    "subtotal_cents": 450000,
    "tax_cents": 0,
    "total_cents": 450000,
    "currency": "USD"
  }
]
```

#### Get Invoice
Get invoice details.

**Endpoint**: `GET /invoices/{invoice_id}`

#### Update Invoice Status
Change invoice status.

**Endpoint**: `PATCH /invoices/{invoice_id}`

**Request**:
```json
{
  "status": "sent"
}
```

#### Download Invoice PDF
Get invoice as PDF.

**Endpoint**: `GET /invoices/{invoice_id}/pdf`

**Response**: `200 OK` (PDF file)

#### Get Invoice Line Items
Get line items for invoice.

**Endpoint**: `GET /invoices/{invoice_id}/line-items`

---

### Payments (`/payments`)

#### List Payments
Get all payments for an invoice.

**Endpoint**: `GET /invoices/{invoice_id}/payments`

**Response**: `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440040",
    "invoice_id": "550e8400-e29b-41d4-a716-446655440030",
    "amount_cents": 225000,
    "payment_date": "2024-01-20T00:00:00Z",
    "payment_method": "bank_transfer",
    "status": "completed",
    "transaction_id": "TXN-12345"
  }
]
```

#### Record Payment
Record a payment received.

**Endpoint**: `POST /invoices/{invoice_id}/payments`

**Request**:
```json
{
  "amount_cents": 450000,
  "payment_method": "bank_transfer",
  "transaction_id": "TXN-54321",
  "payment_date": "2024-01-20T00:00:00Z"
}
```

**Response**: `201 Created`

---

### Billing Rules (`/billing-rules`)

#### List Billing Rules
Get all billing rules.

**Endpoint**: `GET /billing-rules`

#### Create Billing Rule
Create a new billing rule.

**Endpoint**: `POST /billing-rules`

**Request**:
```json
{
  "client_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Standard Billing",
  "billable_hours_per_month": 160,
  "base_rate_cents": 150000,
  "overtime_rate_cents": 225000
}
```

#### Update Billing Rule
Update rule details.

**Endpoint**: `PATCH /billing-rules/{rule_id}`

---

### Integrations (`/integrations`)

#### Get Integration Status
Get status of all integrations.

**Endpoint**: `GET /integrations/status`

#### Connect Google Calendar
Start Google Calendar OAuth flow.

**Endpoint**: `GET /integrations/google/auth`

#### Connect Outlook
Start Microsoft Outlook OAuth flow.

**Endpoint**: `GET /integrations/outlook/auth`

#### Sync Calendar
Trigger manual sync of calendar events.

**Endpoint**: `POST /integrations/sync`

**Request**:
```json
{
  "integration_type": "google_calendar"
}
```

---

## Error Handling

### Error Response Format

All errors return a JSON response with status code and details:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

### Example Error Response

```bash
curl http://localhost:8000/api/v1/invoices/invalid-id \
  -H "Authorization: Bearer <token>"
```

**Response**: `404 Not Found`
```json
{
  "detail": "Invoice not found"
}
```

---

## Rate Limiting

Rate limits are per authenticated user:
- **Requests**: 1000 per hour
- **Burst**: 100 requests per minute

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705318800
```

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `skip` (int): Number of items to skip (default: 0)
- `limit` (int): Max items to return (default: 50, max: 100)

**Example**:
```bash
curl "http://localhost:8000/api/v1/invoices?skip=50&limit=25"
```

---

## Filtering & Searching

Many endpoints support filtering:

```bash
# Filter by status
curl "http://localhost:8000/api/v1/invoices?status=paid"

# Filter by date range
curl "http://localhost:8000/api/v1/time-entries?start_date=2024-01-01&end_date=2024-01-31"

# Multiple filters
curl "http://localhost:8000/api/v1/invoices?status=paid&client_id=123&limit=25"
```

---

## Field Validation

Common validation rules:

### Email
- Must be valid email format
- Must be unique per user

### Currency
- Must be valid ISO 4217 code (USD, EUR, etc.)

### Amounts
- Must be integers (in cents)
- Must be non-negative

### Dates
- Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- End dates must be after start dates

---

## WebHooks (Future)

Webhook support coming soon for:
- Invoice status changes
- Payment received
- Integration sync events
- Time entry creation

---

## Interactive API Documentation

Access interactive documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

---

## SDKs & Client Libraries

Official SDKs available for:
- JavaScript/TypeScript (npm package)
- Python (pip package)
- More coming soon

---

## Support

- **Documentation**: https://docs.billops.com
- **Status Page**: https://status.billops.com
- **Email**: support@billops.com
- **Slack**: https://slack.billops.com
