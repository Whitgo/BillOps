# BillOps API Routes Documentation

## Base URL
All routes are prefixed with `/api/v1`

## Authentication Routes
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Authenticate user and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current authenticated user

## Clients Routes
- `GET /clients/` - List all clients (paginated)
  - Query params: `skip`, `limit`
- `POST /clients/` - Create a new client (201)
- `GET /clients/{client_id}` - Get client by ID
- `PATCH /clients/{client_id}` - Update client
- `DELETE /clients/{client_id}` - Delete client (204)

## Projects Routes
- `GET /projects/` - List all projects (paginated)
  - Query params: `client_id`, `skip`, `limit`
- `POST /projects/` - Create a new project (201)
- `GET /projects/{project_id}` - Get project by ID
- `PATCH /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project (204)

## Time Entries Routes
- `GET /time-entries/` - List time entries with filtering (paginated)
  - Query params: `user_id`, `project_id`, `status`, `skip`, `limit`
- `POST /time-entries/` - Create a new time entry (201)
- `GET /time-entries/{entry_id}` - Get time entry by ID
- `PATCH /time-entries/{entry_id}` - Update time entry
- `DELETE /time-entries/{entry_id}` - Delete time entry (204)

## Billing Rules Routes
- `GET /billing-rules/` - List billing rules with filtering (paginated)
  - Query params: `project_id`, `active_only`, `skip`, `limit`
- `POST /billing-rules/` - Create a new billing rule (201)
- `GET /billing-rules/{rule_id}` - Get billing rule by ID
- `PATCH /billing-rules/{rule_id}` - Update billing rule
- `DELETE /billing-rules/{rule_id}` - Delete billing rule (204)

## Invoices Routes
- `GET /invoices/` - List invoices with filtering (paginated)
  - Query params: `client_id`, `status`, `skip`, `limit`
- `POST /invoices/` - Create a new invoice (201)
- `GET /invoices/{invoice_id}` - Get invoice by ID
- `GET /invoices/number/{invoice_number}` - Get invoice by invoice number
- `PATCH /invoices/{invoice_id}` - Update invoice
- `DELETE /invoices/{invoice_id}` - Delete invoice (204)

## Payments Routes
- `GET /payments/` - List payments with optional filtering (paginated)
  - Query params: `invoice_id`, `skip`, `limit`
- `POST /payments/` - Create a new payment (201)
- `GET /payments/{payment_id}` - Get payment by ID
- `PATCH /payments/{payment_id}` - Update payment
- `DELETE /payments/{payment_id}` - Delete payment (204)

## Features

### Pagination
List endpoints support pagination via query parameters:
- `skip` (default: 0, minimum: 0) - Number of items to skip
- `limit` (default: 50, range: 1-100) - Number of items to return

### Filtering
- **Projects**: Filter by `client_id`
- **Time Entries**: Filter by `user_id`, `project_id`, or `status`
- **Billing Rules**: Filter by `project_id`, optionally get only active rules with `active_only=true`
- **Invoices**: Filter by `client_id` or `status`
- **Payments**: Filter by `invoice_id`

### HTTP Status Codes
- `200 OK` - Successful GET, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error

### Dependencies
All routes use FastAPI dependency injection:
- `get_db()` - Injects SQLAlchemy Session for database operations
- Authentication routes may require bearer token (via `get_current_user`)

## Example Usage

### Create a Client
```bash
curl -X POST http://localhost:8000/api/v1/clients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "currency": "USD",
    "contact_email": "contact@acme.com",
    "contact_name": "John Doe"
  }'
```

### List Clients with Pagination
```bash
curl http://localhost:8000/api/v1/clients/?skip=0&limit=10
```

### Get Active Billing Rules for a Project
```bash
curl "http://localhost:8000/api/v1/billing-rules/?project_id=<uuid>&active_only=true"
```

### List Invoices by Status
```bash
curl "http://localhost:8000/api/v1/invoices/?status=paid"
```
