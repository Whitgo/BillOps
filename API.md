# BillOps API Documentation

## Base URL
```
http://localhost:3001/api
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

### Register
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe",
  "firmName": "Doe Law Firm"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "firmName": "Doe Law Firm"
  },
  "token": "jwt_token"
}
```

### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "token": "jwt_token"
}
```

### Get Current User
```http
GET /auth/me
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "firmName": "Doe Law Firm"
}
```

## Clients

### Get All Clients
```http
GET /clients
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Client Name",
    "email": "client@example.com",
    "phone": "555-1234",
    "companyName": "Company Inc",
    "address": "123 Main St",
    "isActive": true,
    "matters": []
  }
]
```

### Get Single Client
```http
GET /clients/:id
```

### Create Client
```http
POST /clients
```

**Request Body:**
```json
{
  "name": "Client Name",
  "email": "client@example.com",
  "phone": "555-1234",
  "companyName": "Company Inc",
  "address": "123 Main St"
}
```

### Update Client
```http
PUT /clients/:id
```

**Request Body:** Same as Create Client

### Delete Client
```http
DELETE /clients/:id
```

## Matters

### Get All Matters
```http
GET /matters
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Matter Name",
    "description": "Description",
    "matterNumber": "MAT-001",
    "status": "active",
    "hourlyRate": "250.00",
    "client": {
      "id": "uuid",
      "name": "Client Name"
    },
    "timeEntries": []
  }
]
```

### Create Matter
```http
POST /matters
```

**Request Body:**
```json
{
  "clientId": "uuid",
  "name": "Matter Name",
  "description": "Description",
  "matterNumber": "MAT-001",
  "hourlyRate": 250.00,
  "startDate": "2024-01-01",
  "endDate": null
}
```

### Update Matter
```http
PUT /matters/:id
```

### Delete Matter
```http
DELETE /matters/:id
```

## Time Entries

### Get All Time Entries
```http
GET /time-entries?status=approved&matterId=uuid
```

**Query Parameters:**
- `status`: Filter by status (suggested, approved, rejected, billed)
- `matterId`: Filter by matter ID

**Response:**
```json
[
  {
    "id": "uuid",
    "date": "2024-01-15",
    "duration": 60,
    "description": "Meeting with client",
    "taskType": "Client Conference",
    "status": "approved",
    "hourlyRate": "250.00",
    "amount": "250.00",
    "matter": {
      "id": "uuid",
      "name": "Matter Name"
    }
  }
]
```

### Create Time Entry
```http
POST /time-entries
```

**Request Body:**
```json
{
  "matterId": "uuid",
  "date": "2024-01-15",
  "duration": 60,
  "description": "Meeting with client",
  "taskType": "Client Conference",
  "isBillable": true
}
```

### Update Time Entry
```http
PUT /time-entries/:id
```

### Approve Time Entry
```http
POST /time-entries/:id/approve
```

### Reject Time Entry
```http
POST /time-entries/:id/reject
```

### Delete Time Entry
```http
DELETE /time-entries/:id
```

## Invoices

### Get All Invoices
```http
GET /invoices
```

**Response:**
```json
[
  {
    "id": "uuid",
    "invoiceNumber": "INV-2024-001",
    "issueDate": "2024-01-20",
    "dueDate": "2024-02-20",
    "status": "sent",
    "subtotal": "1000.00",
    "taxAmount": "0.00",
    "total": "1000.00",
    "client": {
      "id": "uuid",
      "name": "Client Name"
    },
    "timeEntries": [],
    "payments": []
  }
]
```

### Create Invoice
```http
POST /invoices
```

**Request Body:**
```json
{
  "clientId": "uuid",
  "timeEntryIds": ["uuid1", "uuid2"],
  "dueDate": "2024-02-20",
  "notes": "Payment due upon receipt"
}
```

### Download Invoice PDF
```http
GET /invoices/:id/pdf
```

**Response:** Binary PDF file

### Update Invoice
```http
PUT /invoices/:id
```

### Delete Invoice
```http
DELETE /invoices/:id
```

## Payments

### Create Payment Intent
```http
POST /payments/create-payment-intent
```

**Request Body:**
```json
{
  "invoiceId": "uuid"
}
```

**Response:**
```json
{
  "clientSecret": "stripe_client_secret",
  "paymentId": "uuid"
}
```

### Stripe Webhook
```http
POST /payments/webhook
```

**Note:** This endpoint is called by Stripe, not by the client application.

### Get All Payments
```http
GET /payments
```

### Get Payment Details
```http
GET /payments/:id
```

## Integrations

### Get Gmail Authorization URL
```http
GET /integrations/gmail/auth-url
```

**Response:**
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

### Gmail OAuth Callback
```http
POST /integrations/gmail/callback
```

**Request Body:**
```json
{
  "code": "oauth_authorization_code"
}
```

### Get Calendar Authorization URL
```http
GET /integrations/calendar/auth-url
```

### Calendar OAuth Callback
```http
POST /integrations/calendar/callback
```

### Get Drive Authorization URL
```http
GET /integrations/drive/auth-url
```

### Drive OAuth Callback
```http
POST /integrations/drive/callback
```

### Trigger Manual Sync
```http
POST /integrations/sync
```

**Response:**
```json
{
  "message": "Sync started"
}
```

### Get Time Entry Suggestions
```http
GET /integrations/suggestions
```

**Response:**
```json
[
  {
    "id": "uuid",
    "date": "2024-01-15",
    "duration": 15,
    "description": "Email communication: Project discussion",
    "taskType": "Communication",
    "status": "suggested",
    "matter": {
      "id": "uuid",
      "name": "Matter Name"
    },
    "activity": {
      "activityType": "email",
      "subject": "Project discussion"
    }
  }
]
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider adding rate limiting for production use.

## Pagination

Currently all list endpoints return all results. Consider implementing pagination for production use:

```http
GET /clients?page=1&perPage=20
```
