# Invoice Generation - Practical Examples & Testing Guide

## Example 1: Basic Invoice Generation

### Scenario
Generate an invoice for a client with approved time entries using the default professional template.

### Code
```python
from uuid import UUID
from app.services.tasks.billing import generate_invoice_task

# Queue the task
invoice_id = "550e8400-e29b-41d4-a716-446655440000"
task = generate_invoice_task.delay(invoice_id)

# Check status
print(f"Task ID: {task.id}")
print(f"Task status: {task.status}")

# Get result when ready
try:
    result = task.get(timeout=30)
    print("Invoice generation result:")
    print(f"  Status: {result['status']}")
    print(f"  Invoice: {result['invoice_number']}")
    print(f"  Total: ${result['total_cents'] / 100:.2f}")
    if result.get('pdf_url'):
        print(f"  PDF URL: {result['pdf_url']}")
except Exception as e:
    print(f"Task failed: {e}")
```

---

## Example 2: Custom Template Layout

### Scenario
Generate an invoice for a creative agency using the premium branded template.

### Code
```python
from app.services.tasks.billing import generate_invoice_task

invoice_id = "550e8400-e29b-41d4-a716-446655440000"

# Use branded template
task = generate_invoice_task.delay(
    invoice_id,
    template_layout="branded"
)

result = task.get()
print(f"Generated invoice with {result['template_layout']} layout")
```

---

## Example 3: Custom Company Information

### Scenario
Generate invoice with custom company details instead of defaults.

### Code
```python
from app.services.tasks.billing import generate_invoice_task

invoice_id = "550e8400-e29b-41d4-a716-446655440000"

company_details = {
    "name": "Acme Creative Studio",
    "email": "billing@acmecreative.com",
    "address": "456 Design Ave, San Francisco, CA 94102"
}

task = generate_invoice_task.delay(
    invoice_id,
    template_layout="branded",
    company_info=company_details
)

result = task.get()
print(f"Generated branded invoice for {company_details['name']}")
```

---

## Example 4: API Endpoint for Invoice Generation

### Scenario
Create a FastAPI endpoint to trigger invoice generation from HTTP request.

### Code
```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.tasks.billing import generate_invoice_task

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

class InvoiceGenerateRequest(BaseModel):
    invoice_id: str
    template_layout: str = "professional"
    company_name: str = None
    company_email: str = None
    company_address: str = None

class TaskResponse(BaseModel):
    task_id: str
    message: str
    invoice_id: str

@router.post("/{invoice_id}/generate", response_model=TaskResponse)
async def generate_invoice(
    invoice_id: str,
    request: InvoiceGenerateRequest = None
):
    """Generate and send invoice PDF.
    
    Query Parameters:
    - template_layout: "minimalist", "professional", or "branded"
    - company_name: Override company name
    - company_email: Override company email
    - company_address: Override company address
    
    Returns:
    - task_id: Celery task ID (poll /tasks/{task_id} for status)
    - message: Human-readable status message
    """
    # Build company info if provided
    company_info = None
    if request and (request.company_name or request.company_email or request.company_address):
        company_info = {
            "name": request.company_name or "BillOps",
            "email": request.company_email or "billing@example.com",
            "address": request.company_address or "123 Main St, City, Country"
        }
    
    # Queue the task
    task = generate_invoice_task.delay(
        invoice_id=invoice_id,
        template_layout=request.template_layout if request else "professional",
        company_info=company_info
    )
    
    return TaskResponse(
        task_id=task.id,
        message="Invoice generation queued",
        invoice_id=invoice_id
    )

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of an invoice generation task."""
    from celery.result import AsyncResult
    from app.celery_app import celery
    
    task_result = AsyncResult(task_id, app=celery)
    
    if task_result.state == 'PENDING':
        response = {'state': 'PENDING', 'message': 'Task not found or still pending'}
    elif task_result.state == 'FAILURE':
        response = {
            'state': 'FAILURE',
            'message': str(task_result.info),
            'error': True
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'state': 'SUCCESS',
            'result': task_result.result
        }
    else:
        response = {'state': task_result.state}
    
    return response
```

### Usage
```bash
# Queue invoice generation with professional layout
curl -X POST http://localhost:8000/api/v1/invoices/550e8400-e29b-41d4-a716-446655440000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template_layout": "professional"
  }'

# Response
# {
#   "task_id": "abc123def456",
#   "message": "Invoice generation queued",
#   "invoice_id": "550e8400-e29b-41d4-a716-446655440000"
# }

# Check status
curl http://localhost:8000/api/v1/invoices/tasks/abc123def456

# With custom company info
curl -X POST http://localhost:8000/api/v1/invoices/550e8400-e29b-41d4-a716-446655440000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template_layout": "branded",
    "company_name": "Acme Corp",
    "company_email": "billing@acme.com",
    "company_address": "123 Main St, NYC"
  }'
```

---

## Example 5: Batch Invoice Generation

### Scenario
Generate multiple invoices for a period (e.g., monthly invoicing).

### Code
```python
from app.services.tasks.billing import generate_invoice_task
from app.db.session import SessionLocal
from app.models.invoice import Invoice

def batch_generate_invoices(status="draft"):
    """Generate all draft invoices."""
    db = SessionLocal()
    try:
        # Find all invoices with specified status
        invoices = db.query(Invoice).filter(
            Invoice.status == status
        ).all()
        
        print(f"Generating {len(invoices)} invoices...")
        
        tasks = []
        for invoice in invoices:
            task = generate_invoice_task.delay(
                invoice_id=str(invoice.id),
                template_layout="professional"
            )
            tasks.append(task)
            print(f"  Queued: {invoice.invoice_number} (Task: {task.id})")
        
        # Monitor progress
        results = []
        for i, task in enumerate(tasks):
            try:
                result = task.get(timeout=60)
                results.append(result)
                status_emoji = "✅" if result['status'] == "success" else "❌"
                print(f"  {status_emoji} {result['invoice_number']}: ${result['total_cents']/100:.2f}")
            except Exception as e:
                print(f"  ❌ Task {i} failed: {e}")
        
        # Summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        print(f"\nGenerated {successful}/{len(invoices)} invoices successfully")
        
    finally:
        db.close()

# Run batch generation
batch_generate_invoices(status="draft")
```

---

## Example 6: Scheduled Invoice Generation

### Scenario
Automatically generate invoices on the first of each month.

### Code
```python
from celery.schedules import crontab
from app.celery_app import celery
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.services.tasks.billing import generate_invoice_task
from datetime import datetime, timedelta
from uuid import UUID

@celery.task(name="tasks.billing.monthly_invoice_generation")
def monthly_invoice_generation():
    """Generate all invoices for the previous month."""
    db = SessionLocal()
    try:
        today = datetime.now()
        month_start = today.replace(day=1) - timedelta(days=1)
        month_start = month_start.replace(day=1)
        month_end = today.replace(day=1) - timedelta(days=1)
        
        # Find invoices created in previous month
        invoices = db.query(Invoice).filter(
            Invoice.created_at >= month_start,
            Invoice.created_at <= month_end,
            Invoice.status == "draft"
        ).all()
        
        print(f"Monthly invoicing: {len(invoices)} invoices")
        
        for invoice in invoices:
            generate_invoice_task.delay(
                invoice_id=str(invoice.id),
                template_layout="professional"
            )
        
        return {
            "status": "success",
            "invoices_queued": len(invoices),
            "period": f"{month_start.date()} to {month_end.date()}"
        }
    
    finally:
        db.close()

# Add to Celery Beat schedule
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'monthly-invoice-generation': {
        'task': 'tasks.billing.monthly_invoice_generation',
        'schedule': crontab(hour=0, minute=0, day_of_month=1),  # 1st of each month
    },
}
```

---

## Example 7: Template Selection Based on Invoice Type

### Scenario
Different templates based on client type or project.

### Code
```python
from app.services.tasks.billing import generate_invoice_task
from app.db.session import SessionLocal
from app.models.invoice import Invoice
from app.models.client import Client

def generate_invoice_with_template_selection(invoice_id: str):
    """Auto-select template based on client or project type."""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {"error": "Invoice not found"}
        
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        
        # Template selection logic
        template_layout = "professional"  # Default
        
        # Select based on client type (custom field in meta)
        if client and client.meta:
            client_type = client.meta.get("type")
            
            if client_type == "creative":
                template_layout = "branded"
            elif client_type == "corporate":
                template_layout = "professional"
            elif client_type == "freelance":
                template_layout = "minimalist"
        
        print(f"Selected '{template_layout}' template for {client.name}")
        
        # Generate with selected template
        task = generate_invoice_task.delay(
            invoice_id=invoice_id,
            template_layout=template_layout
        )
        
        return {"task_id": task.id, "template": template_layout}
    
    finally:
        db.close()

# Usage
result = generate_invoice_with_template_selection("550e8400-e29b-41d4-a716-446655440000")
```

---

## Example 8: Error Handling and Retries

### Scenario
Proper error handling and monitoring of invoice generation.

### Code
```python
from app.services.tasks.billing import generate_invoice_task
import logging

logger = logging.getLogger(__name__)

def safe_generate_invoice(invoice_id: str, max_retries: int = 3) -> dict:
    """Generate invoice with error handling and logging."""
    try:
        task = generate_invoice_task.delay(invoice_id)
        logger.info(f"Queued invoice generation: {invoice_id} (Task: {task.id})")
        
        # Wait for result with timeout
        result = task.get(timeout=120)
        
        if result['status'] == 'success':
            logger.info(
                f"✅ Generated {result['invoice_number']}: "
                f"${result['total_cents']/100:.2f}"
            )
            return result
        else:
            logger.error(
                f"❌ Invoice generation failed: {result.get('message')}"
            )
            return result
    
    except Exception as e:
        logger.error(f"Error generating invoice {invoice_id}: {e}", exc_info=True)
        
        return {
            "status": "error",
            "invoice_id": invoice_id,
            "message": str(e)
        }

# Usage with error handling
result = safe_generate_invoice("550e8400-e29b-41d4-a716-446655440000")

if result['status'] == 'success':
    print(f"Invoice PDF: {result.get('pdf_url')}")
else:
    print(f"Failed: {result['message']}")
```

---

## Example 9: Testing with Mock Data

### Scenario
Unit test for invoice generation with mock data.

### Code
```python
import pytest
from unittest.mock import Mock, patch
from app.services.invoices.generator import (
    render_invoice_html, 
    build_invoice_context,
    generate_invoice_pdf
)

def test_render_minimalist_template():
    """Test rendering minimalist template."""
    context = {
        "company": {"name": "Test Co", "email": "test@test.com", "address": "123 St"},
        "client": {"name": "Client", "contact_email": "client@test.com"},
        "project": {"name": "Project"},
        "invoice": {
            "number": "INV-001",
            "currency": "USD",
            "issue_date": "2024-01-15",
            "due_date": "2024-02-15",
            "notes": "Test invoice"
        },
        "items": [
            {
                "description": "Work",
                "quantity": "40.00",
                "unit_price_cents": 10000,
                "amount_cents": 400000
            }
        ],
        "subtotal_cents": 400000,
        "tax_cents": 0,
        "total_cents": 400000
    }
    
    html = render_invoice_html(context, layout="minimalist")
    
    assert "INV-001" in html
    assert "Test Co" in html
    assert "Client" in html
    assert "400000" not in html or "4000" in html  # Should be formatted

def test_professional_template():
    """Test professional template rendering."""
    context = {...}  # Same as above
    
    html = render_invoice_html(context, layout="professional")
    
    assert "INVOICE" in html
    assert "CLIENT" in html or "Bill" in html

def test_branded_template():
    """Test branded template rendering."""
    context = {...}  # Same as above
    
    html = render_invoice_html(context, layout="branded")
    
    # Branded has specific elements
    assert "Professional Billing Solutions" in html or "COMPANY NAME" in html

def test_invalid_layout_defaults_to_professional():
    """Test that invalid layout falls back to professional."""
    context = {...}  # Same as above
    
    html = render_invoice_html(context, layout="invalid_layout")
    
    # Should still render (with professional template)
    assert "INV-001" in html

def test_build_context_with_missing_fields():
    """Test context building handles missing fields gracefully."""
    mock_invoice = Mock()
    mock_invoice.invoice_number = "INV-001"
    mock_invoice.currency = "USD"
    mock_invoice.issue_date = "2024-01-15"
    mock_invoice.due_date = None
    mock_invoice.notes = None
    mock_invoice.tax_cents = 0
    
    mock_client = Mock()
    mock_client.name = "Client"
    mock_client.contact_email = None
    
    context = build_invoice_context(
        invoice=mock_invoice,
        client=mock_client,
        project=None,
        line_items=[]
    )
    
    assert context["invoice"]["number"] == "INV-001"
    assert context["client"]["name"] == "Client"
    assert context["subtotal_cents"] == 0
```

---

## Example 10: Monitoring and Logging

### Scenario
Monitor invoice generation with detailed logging and metrics.

### Code
```python
import logging
from datetime import datetime
from app.services.tasks.billing import generate_invoice_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('invoice_generation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def generate_invoice_with_metrics(invoice_id: str):
    """Generate invoice and log metrics."""
    start_time = datetime.now()
    logger.info(f"Starting invoice generation: {invoice_id}")
    
    try:
        task = generate_invoice_task.delay(invoice_id)
        result = task.get(timeout=120)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result['status'] == 'success':
            logger.info(
                f"✅ Invoice {result['invoice_number']} generated successfully\n"
                f"   Total: ${result['total_cents']/100:.2f}\n"
                f"   Items: {result['line_items']}\n"
                f"   PDF URL: {result.get('pdf_url') or 'Not stored'}\n"
                f"   Time: {elapsed:.2f}s"
            )
        else:
            logger.error(
                f"❌ Failed to generate {invoice_id}: {result.get('message')}\n"
                f"   Time: {elapsed:.2f}s"
            )
        
        return result
    
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"❌ Exception during generation {invoice_id}: {e}\n"
            f"   Time: {elapsed:.2f}s",
            exc_info=True
        )
        raise

# Usage
try:
    result = generate_invoice_with_metrics("550e8400-e29b-41d4-a716-446655440000")
except Exception as e:
    logger.critical(f"Critical error: {e}")
```

---

## Testing Checklist

Before deploying to production:

- [ ] Generate invoice with minimalist template
- [ ] Generate invoice with professional template
- [ ] Generate invoice with branded template
- [ ] Test with custom company information
- [ ] Verify S3 upload (if configured)
- [ ] Test invoice PDF download/viewing
- [ ] Generate invoice with no time entries (should error)
- [ ] Test retry logic (simulate failure)
- [ ] Monitor Celery worker logs
- [ ] Check invoice status updates
- [ ] Verify time entries marked as 'billed'
- [ ] Test with large time entry sets (performance)

---

## Troubleshooting

### Task shows as pending forever
```python
# Check Celery worker is running
celery -A app.celery_app worker -l info

# Check Redis connection
redis-cli ping  # Should return "PONG"

# Check task in queue
celery -A app.celery_app inspect active
```

### PDF is None
```python
# S3 may not be configured (this is OK)
# Check if local PDF generation succeeded
# Look for "generated_at" in invoice.meta

if invoice.meta and invoice.meta.get("generated_at"):
    print("PDF was generated successfully")
else:
    print("PDF generation failed")
```

### Template rendering fails
```python
# Check Jinja2 syntax in template
# Verify context has all required fields
# Check template path and file permissions
# Look for "Failed to render" in logs
```

### Invoice already has line items
```python
# Can't regenerate if line items exist
# Delete line items first or use new invoice
db.query(InvoiceLineItem).filter(
    InvoiceLineItem.invoice_id == invoice_id
).delete()
db.commit()
```
