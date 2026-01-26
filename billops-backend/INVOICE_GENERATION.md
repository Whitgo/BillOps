# Invoice Generation System

Complete invoice generation pipeline that assembles time entries, applies billing rules, generates PDFs with multiple template layouts, and uploads to S3.

## Architecture

The invoice generation system consists of three main components:

### 1. HTML Invoice Templates (`app/services/invoices/templates/`)

Three professionally designed invoice templates optimized for different use cases:

#### **Minimalist Layout** (`invoice_minimalist.html`)
- Clean, elegant design focused on essential information
- Minimal borders and decorative elements
- Professional monochrome color scheme
- Ideal for: Law firms, consulting, professional services
- Key Features:
  - Clear hierarchical typography
  - Prominent invoice number
  - Compact line item table
  - Simple footer with company details

#### **Professional Layout** (`invoice_professional.html`)
- Modern, feature-rich design with structured sections
- Color-coded headers and alternating row backgrounds
- Detailed invoice information card
- Ideal for: Business-to-business, corporate invoicing
- Key Features:
  - Grid-based layout with info cards
  - Highlighted totals section
  - Notes and terms section
  - Footer with company contact information

#### **Branded Layout** (`invoice_branded.html`)
- Eye-catching gradient header with brand colors
- Premium appearance with visual accents
- Highlighted invoice badge
- Ideal for: Creative agencies, design studios, premium services
- Key Features:
  - Gradient background on header
  - Branded company name display
  - Color-accented summary box
  - Modern styling with border accents

### 2. PDF Generator (`app/services/invoices/generator.py`)

Renders HTML templates and generates PDF documents using WeasyPrint.

**Functions:**

```python
render_invoice_html(context: dict[str, Any], layout: str = "professional") -> str
```
Renders invoice HTML from a Jinja2 template.

**Parameters:**
- `context`: Template context with invoice, client, line items data
- `layout`: Template layout ('minimalist', 'professional', or 'branded')

**Returns:** Rendered HTML string

```python
generate_pdf_from_html(html: str) -> bytes
```
Generates PDF bytes from HTML using WeasyPrint.

**Parameters:**
- `html`: HTML content string

**Returns:** PDF file bytes

```python
build_invoice_context(invoice, client, project, line_items, company) -> dict
```
Builds Jinja2 template context from ORM objects.

**Parameters:**
- `invoice`: Invoice model instance
- `client`: Client model instance
- `project`: Project model instance (optional)
- `line_items`: List of InvoiceLineItem instances
- `company`: Company info dict (optional, uses defaults)

**Returns:** Dictionary with template context

```python
generate_invoice_pdf(invoice, client, project, line_items, company, layout) -> bytes
```
Complete invoice PDF generation pipeline.

**Parameters:**
- `invoice`: Invoice model instance
- `client`: Client model instance
- `project`: Project model instance (optional)
- `line_items`: List of InvoiceLineItem instances
- `company`: Company info dict (optional)
- `layout`: Template layout ('minimalist', 'professional', 'branded')

**Returns:** PDF file bytes

### 3. Celery Task (`app/services/tasks/billing.py`)

Asynchronous task that orchestrates the entire invoice generation workflow.

**Task:** `tasks.billing.generate_invoice`

```python
generate_invoice_task(invoice_id: str, template_layout: str = "professional", company_info: dict = None) -> dict
```

**Workflow:**

1. **Validation**: Verify invoice exists and template layout is valid
2. **Collection**: Gather approved time entries for client/project within optional period
3. **Billing Rules**: Apply active billing rule to calculate amounts and rounding
4. **Line Items**: Create invoice line items with:
   - Description from time entry
   - Quantity in hours (with rounding based on rule)
   - Unit price from billing rule
   - Amount (computed: hours × rate)
   - Billing rule snapshot for audit trail
5. **PDF Generation**: Render HTML with specified template layout
6. **PDF Upload**: Upload PDF to S3 and store URL in invoice metadata
7. **Status Update**: Update invoice status to 'sent' and mark time entries as 'billed'
8. **Retry Logic**: Automatic retry up to 3 times on failure with exponential backoff

**Parameters:**

- `invoice_id` (string): UUID of the invoice to generate
- `template_layout` (string): Template layout to use
  - `"minimalist"` - Clean, minimal design
  - `"professional"` - Feature-rich corporate design
  - `"branded"` - Premium branded design
  - Default: `"professional"`
- `company_info` (dict, optional): Company metadata
  - `name`: Company name
  - `email`: Contact email
  - `address`: Physical address
  - Default: Uses settings configured in app

**Returns:**

Success response:
```json
{
  "status": "success",
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2024-001",
  "line_items": 5,
  "subtotal_cents": 250000,
  "total_cents": 250000,
  "pdf_url": "https://bucket.s3.region.amazonaws.com/invoices/INV-2024-001.pdf",
  "template_layout": "professional"
}
```

Error response:
```json
{
  "status": "error",
  "message": "No approved time entries found for invoice"
}
```

## Usage

### Basic Invocation

```python
from app.services.tasks.billing import generate_invoice_task

# Queue the task with default professional layout
result = generate_invoice_task.delay(invoice_id="550e8400-e29b-41d4-a716-446655440000")

# Check result
print(result.get())
```

### With Custom Template Layout

```python
# Queue with minimalist layout
result = generate_invoice_task.delay(
    invoice_id="550e8400-e29b-41d4-a716-446655440000",
    template_layout="minimalist"
)
```

### With Custom Company Info

```python
# Queue with custom company information
result = generate_invoice_task.delay(
    invoice_id="550e8400-e29b-41d4-a716-446655440000",
    template_layout="branded",
    company_info={
        "name": "Acme Corporation",
        "email": "billing@acme.com",
        "address": "123 Main St, New York, NY 10001"
    }
)
```

### From API Endpoint

```python
from fastapi import APIRouter, HTTPException
from app.services.tasks.billing import generate_invoice_task

router = APIRouter()

@router.post("/invoices/{invoice_id}/generate")
async def generate_invoice_endpoint(
    invoice_id: str,
    template_layout: str = "professional",
    company_info: dict = None
):
    """Generate and send invoice PDF"""
    task = generate_invoice_task.delay(
        invoice_id=invoice_id,
        template_layout=template_layout,
        company_info=company_info
    )
    return {
        "task_id": task.id,
        "message": "Invoice generation queued"
    }
```

## Template Context

Templates receive the following context structure:

```python
{
    "company": {
        "name": "BillOps",
        "email": "billing@example.com",
        "address": "123 Main St, City, Country"
    },
    "client": {
        "name": "Client Corporation",
        "contact_email": "contact@client.com"
    },
    "project": {
        "name": "Project Name"  # or None if no project
    },
    "invoice": {
        "number": "INV-2024-001",
        "currency": "USD",
        "issue_date": datetime(2024, 1, 15),
        "due_date": datetime(2024, 2, 15),
        "notes": "Thank you for your business"
    },
    "items": [
        {
            "description": "Development Work",
            "quantity": "40.00",
            "unit_price_cents": 10000,  # $100.00
            "amount_cents": 400000  # $4,000.00
        }
    ],
    "subtotal_cents": 400000,
    "tax_cents": 0,
    "total_cents": 400000
}
```

## Template Filters

### `cents_to_currency`
Converts cents to formatted currency string.

Usage: `{{ amount_cents|cents_to_currency(invoice.currency) }}`

Example: `{{ 10000|cents_to_currency('USD') }}` → `USD $100.00`

### `format_date`
Formats datetime objects to readable date strings.

Usage: `{{ invoice.issue_date|format_date }}`

Example: `{{ datetime(2024, 1, 15)|format_date }}` → `Jan 15, 2024`

## Requirements

### Python Dependencies
- **FastAPI**: Web framework
- **Celery**: Task queue
- **SQLAlchemy**: ORM
- **Jinja2**: Template engine (3.1.4+)
- **WeasyPrint**: PDF generation (60.2+)
- **boto3**: AWS S3 integration
- **Redis**: Celery broker

### Configuration

**Environment Variables (in `app/config/settings.py`):**

```python
S3_BUCKET_NAME = "your-bucket-name"
S3_BASE_PATH = "invoices"  # Optional base path in bucket
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "your-key"
AWS_SECRET_ACCESS_KEY = "your-secret"
```

### S3 Permissions

The AWS IAM user requires S3 permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/invoices/*"
    }
  ]
}
```

## Error Handling

The task includes robust error handling with:

1. **Validation**: Checks for missing invoices and invalid layouts
2. **Retry Logic**: Automatic exponential backoff (60s, 120s, 240s)
3. **Logging**: Detailed logging at info and error levels
4. **Graceful Degradation**: Continues even if S3 is not configured

## Database Schema

### Invoice Model
```
id: UUID (primary key)
client_id: UUID (foreign key)
project_id: UUID (foreign key, nullable)
invoice_number: String (unique)
status: String (draft|sent|paid|partial|overdue|canceled)
issue_date: DateTime
due_date: DateTime (nullable)
subtotal_cents: Integer
tax_cents: Integer
total_cents: Integer
notes: Text (nullable)
meta: JSON (nullable)
created_at: DateTime
updated_at: DateTime
```

### InvoiceLineItem Model
```
id: UUID (primary key)
invoice_id: UUID (foreign key)
time_entry_id: UUID (foreign key, nullable)
description: String
quantity: String (e.g., "40.00 h")
unit_price_cents: Integer
amount_cents: Integer
billing_rule_snapshot: JSON
```

### TimeEntry Model
```
status: String (pending|approved|rejected|billed)
billing_rule_id: UUID (nullable, foreign key)
```

## Workflow Diagram

```
┌──────────────────────────┐
│  Invoice Created         │
│  (draft status)          │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ generate_invoice_task()  │
└────────────┬─────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
Validate         Retrieve Data
Invoice          (Client, Project)
    │                 │
    └────────┬────────┘
             ▼
    Collect Time Entries
    (status=approved)
             │
             ▼
    Apply Billing Rules
    & Calculate Amounts
             │
             ▼
    Create Line Items
             │
             ▼
    Render HTML
    (Selected Layout)
             │
             ▼
    Generate PDF
    (WeasyPrint)
             │
             ▼
    Upload to S3
             │
             ▼
    Update Invoice Meta
    Mark Entries as Billed
             │
             ▼
    Set Status = 'sent'
             │
             ▼
  ┌─────────────────────┐
  │ Return Success      │
  │ with PDF URL        │
  └─────────────────────┘
```

## Performance Considerations

1. **Async Processing**: Task runs in Celery worker, non-blocking
2. **Database**: Single query for invoice, client, project, entries
3. **PDF Generation**: WeasyPrint is CPU-intensive; consider worker sizing
4. **S3 Upload**: Network-bound; retry logic handles transient failures
5. **Caching**: Consider caching templates and billing rules for high volume

## Testing

### Unit Test Example

```python
from app.services.invoices.generator import render_invoice_html

def test_render_minimalist_template():
    context = {
        "company": {"name": "Test Co"},
        "client": {"name": "Client"},
        "project": None,
        "invoice": {"number": "INV-001", "currency": "USD"},
        "items": [],
        "subtotal_cents": 0,
        "tax_cents": 0,
        "total_cents": 0
    }
    
    html = render_invoice_html(context, layout="minimalist")
    assert "INV-001" in html
    assert "Test Co" in html
```

### Integration Test Example

```python
def test_generate_invoice_task(db_session):
    # Create test data
    invoice = create_test_invoice()
    client = create_test_client()
    entries = create_test_time_entries()
    
    # Run task
    result = generate_invoice_task.apply(
        args=(str(invoice.id),),
        kwargs={"template_layout": "professional"}
    )
    
    # Assert result
    assert result.get("status") == "success"
    assert result.get("pdf_url") is not None
    assert invoice.status == "sent"
```

## Customization

### Adding New Template Layout

1. Create new HTML template in `app/services/invoices/templates/`
2. Add to `TEMPLATE_LAYOUTS` dict in `generator.py`
3. Use Jinja2 template with same context structure
4. Reference in task calls: `template_layout="custom_name"`

Example:
```python
# templates/invoice_custom.html
<!-- Create custom invoice design -->

# generator.py
TEMPLATE_LAYOUTS = {
    "minimalist": "invoice_minimalist.html",
    "professional": "invoice_professional.html",
    "branded": "invoice_branded.html",
    "custom": "invoice_custom.html",  # Add new layout
}
```

### Modifying Company Information

Defaults come from `app/config/settings.py`. Override per-task:

```python
generate_invoice_task.delay(
    invoice_id=invoice_id,
    company_info={
        "name": "Custom Name",
        "email": "custom@example.com",
        "address": "Custom Address"
    }
)
```

## Troubleshooting

### PDF Generation Fails
- Check WeasyPrint installation: `pip install WeasyPrint==60.2`
- Verify template syntax (Jinja2 errors in logs)
- Check HTML context completeness

### S3 Upload Fails
- Verify AWS credentials in settings
- Check S3 bucket name and region
- Verify IAM permissions
- Check network connectivity

### Task Never Completes
- Monitor Celery worker logs
- Check Redis connection
- Verify database connection
- Monitor system resources (CPU/memory)

### Invoice PDF URL is None
- S3 is likely not configured (this is acceptable)
- PDF is still generated locally in task
- Configure S3 to enable uploads

## License

Part of the BillOps billing system.
