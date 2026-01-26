# BillOps Quick Start Guide

## What Was Built

A **production-ready billing and invoicing backend** with FastAPI featuring:
- User authentication and authorization
- Client and project management
- Time entry tracking
- Automatic invoice generation
- Payment processing
- Calendar integrations
- Analytics and monitoring
- 150+ comprehensive tests
- Interactive API documentation

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL or SQLite
- Redis (optional, for task queue)

### Installation
```bash
# Navigate to backend
cd billops-backend

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Update .env with your settings
# - Database URL
# - JWT secret
# - AWS S3 credentials (optional)
# - Integration keys
```

### Run the Application

**Development Mode**:
```bash
uvicorn app.main:app --reload --port 8000
```

**Production Mode**:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Access the API
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Core Features

### User Registration & Authentication
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Response includes JWT token for future requests
```

### Client Management
```bash
# Create client
curl -X POST http://localhost:8000/clients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name":"Acme Corp",
    "contact_person":"John Doe",
    "email":"john@acme.com"
  }'

# List clients
curl http://localhost:8000/clients \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Time Tracking
```bash
# Create time entry
curl -X POST http://localhost:8000/time-entries \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id":"uuid-here",
    "start_time":"2024-01-26T09:00:00Z",
    "end_time":"2024-01-26T17:00:00Z",
    "is_billable":true,
    "description":"Project work"
  }'

# List time entries
curl http://localhost:8000/time-entries?skip=0&limit=20 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Invoice Generation
```bash
# Generate invoice from time entries
curl -X POST http://localhost:8000/invoices \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id":"uuid-here",
    "project_id":"uuid-here"
  }'

# Get invoice
curl http://localhost:8000/invoices/uuid-here \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get invoice PDF
curl http://localhost:8000/invoices/uuid-here/pdf \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o invoice.pdf
```

## Testing

### Run All Tests
```bash
# Run full regression suite
python run_regression_tests.py

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test types
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/e2e/ -v           # E2E tests
```

### Test Results
- Tests create HTML coverage report: `htmlcov/index.html`
- JSON reports saved to: `test_reports/regression_report_*.json`

## API Documentation

### Complete Endpoint Reference
See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for:
- All 30+ endpoints
- Request/response examples
- Authentication details
- Error codes
- Pagination and filtering

### Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | User login |
| GET | `/users/me` | Get current user |
| GET/POST | `/clients` | Manage clients |
| GET/POST | `/projects` | Manage projects |
| GET/POST | `/time-entries` | Time tracking |
| GET/POST | `/invoices` | Invoice management |
| GET/POST | `/payments` | Payment recording |
| GET/POST | `/billing-rules` | Billing configuration |

## Configuration

### Environment Variables
Create `.env` file with:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/billops

# JWT
JWT_SECRET=your-super-secret-key
JWT_EXPIRATION_HOURS=24

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_BUCKET_NAME=billops-files

# Email (optional)
SENDGRID_API_KEY=sg_xxx...
EMAIL_FROM=noreply@billops.com

# Integrations (optional)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
SLACK_BOT_TOKEN=xoxb-xxx...
```

## Database Setup

### Automatic Migration
```bash
# Run migrations
alembic upgrade head
```

### Manual Database Creation
```bash
# Connect to PostgreSQL
psql postgresql://user:password@localhost

# Create database
CREATE DATABASE billops;

# Run migrations from app
cd billops-backend
alembic upgrade head
```

## Analytics & Monitoring

### Event Tracking
Events are automatically tracked for:
- User actions (registration, login)
- Business operations (invoice creation, payments)
- API calls (method, endpoint, response time)
- Errors and warnings

Access metrics:
```python
from app.services.analytics import get_analytics, get_metrics

analytics = get_analytics()
metrics = get_metrics()

# Track custom event
analytics.track_invoice_event(
    event_type="INVOICE_CREATED",
    invoice_id="123",
    user_id="456"
)

# Get metrics summary
summary = metrics.get_summary()
```

### Response Time Monitoring
Every API response includes:
```
X-Process-Time: 0.125  # seconds
```

## File Storage

### S3 Integration
Upload and manage files:

```python
from app.utils.storage import get_storage_service

storage = get_storage_service()

# Upload file
url = storage.upload_file(
    "invoices/inv-001.pdf",
    file_bytes,
    content_type="application/pdf"
)

# Download file
file_bytes = storage.download_file("invoices/inv-001.pdf")

# Get presigned URL for direct access
presigned_url = storage.get_presigned_url(
    "invoices/inv-001.pdf",
    expiration_minutes=30
)

# List files
files = storage.list_files("invoices/")

# Delete file
storage.delete_file("invoices/inv-001.pdf")
```

## DateTime Utilities

### Working with Dates and Times
```python
from app.utils.dt import (
    round_to_nearest_hour,
    get_month_boundaries,
    format_duration,
    is_business_day,
    convert_timezone
)

# Round to nearest hour
rounded = round_to_nearest_hour(datetime.now())

# Get month start and end
start, end = get_month_boundaries(datetime.now())

# Format duration
duration_text = format_duration(minutes=125)  # "2h 5m"

# Check if business day
if is_business_day(datetime.now()):
    print("Working day")

# Convert timezone
utc_time = convert_timezone(local_time, from_tz="US/Eastern", to_tz="UTC")
```

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Use different port
uvicorn app.main:app --port 8001
```

**Database Connection Error**
```bash
# Check DATABASE_URL in .env
# Verify PostgreSQL is running
psql postgresql://user:password@localhost
```

**Tests Hanging**
```bash
# Clear pytest cache
pytest --cache-clear tests/

# Run with timeout
pytest tests/ --timeout=300
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Project Structure Reference

```
billops-backend/
├── app/
│   ├── api/v1/routes/        # API endpoint handlers
│   ├── core/                 # JWT, authentication, hashing
│   ├── db/                   # Database models and migrations
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic validation schemas
│   ├── services/             # Business logic (billing, invoicing)
│   ├── utils/                # S3 storage, datetime helpers
│   ├── middleware/           # CORS, logging, analytics
│   ├── workers/              # Celery task configuration
│   └── main.py               # FastAPI app and routes
├── tests/
│   ├── unit/                 # Unit tests (models, services)
│   ├── integration/          # Integration tests (workflows)
│   └── e2e/                  # End-to-end tests
├── migrations/               # Alembic database migrations
└── scripts/                  # Helper scripts
```

## Documentation Files

| File | Purpose |
|------|---------|
| [COMPLETE_SUMMARY.md](./COMPLETE_SUMMARY.md) | Full project overview |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | API endpoint reference |
| [TEST_SUMMARY.md](./TEST_SUMMARY.md) | Testing infrastructure |
| [VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md) | Testing procedures |
| [README.md](./README.md) | Project readme |
| [INTEGRATIONS.md](./INTEGRATIONS.md) | Integration setup |

## Next Steps

### For Development
1. Start the application
2. Access Swagger UI
3. Create test data
4. Explore endpoints
5. Run test suite

### For Deployment
1. Set up PostgreSQL
2. Configure environment variables
3. Run migrations
4. Deploy to server
5. Set up monitoring

### For Integration
1. Connect to your calendar system
2. Configure billing rules
3. Set up email notifications
4. Enable S3 file storage
5. Monitor analytics

## Support

### Useful Commands

```bash
# Start development server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# Format code
black app/ tests/

# Run type checking
mypy app/

# Run linting
flake8 app/ tests/

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Pytest Guide**: https://docs.pytest.org/
- **GitHub Repository**: https://github.com/Whitgo/BillOps

## Summary

You now have a **fully functional billing backend** ready to:
- ✅ Manage clients and projects
- ✅ Track billable time
- ✅ Generate invoices automatically
- ✅ Process payments
- ✅ Integrate with calendars
- ✅ Send notifications
- ✅ Monitor performance
- ✅ Handle analytics

Everything is documented, tested, and ready for production deployment!

**Start the server and visit http://localhost:8000/api/docs to explore the API.**
