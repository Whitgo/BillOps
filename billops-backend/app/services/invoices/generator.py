"""Invoice PDF generator service.

Renders HTML invoice templates and generates PDFs using WeasyPrint.
Supports multiple template layouts: minimalist, professional, and branded.
"""
from __future__ import annotations

from typing import Any, Literal
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from weasyprint import HTML, CSS  # type: ignore
except Exception:  # pragma: no cover
    HTML = None  # type: ignore
    CSS = None  # type: ignore

# Template layout options
TEMPLATE_LAYOUTS = {
    "minimalist": "invoice_minimalist.html",
    "professional": "invoice_professional.html",
    "branded": "invoice_branded.html",
}

DEFAULT_LAYOUT = "professional"


def _get_jinja_env() -> Environment:
    """Create a Jinja2 environment for invoice templates."""
    loader = FileSystemLoader("app/services/invoices/templates")
    env = Environment(loader=loader, autoescape=select_autoescape(["html"]))
    env.filters["cents_to_currency"] = lambda c, cur="USD": f"{cur} ${(c or 0)/100:,.2f}"
    env.filters["format_date"] = lambda d: d.strftime("%b %d, %Y") if isinstance(d, datetime) else str(d)
    return env


def render_invoice_html(context: dict[str, Any], layout: str = DEFAULT_LAYOUT) -> str:
    """Render invoice HTML from Jinja2 template using provided context.
    
    Args:
        context: Template context dictionary.
        layout: Template layout to use ('minimalist', 'professional', or 'branded').
                Defaults to 'professional' if unknown layout is specified.
    
    Returns:
        Rendered HTML string.
    """
    env = _get_jinja_env()
    template_name = TEMPLATE_LAYOUTS.get(layout, TEMPLATE_LAYOUTS[DEFAULT_LAYOUT])
    template = env.get_template(template_name)
    return template.render(**context)


def generate_pdf_from_html(html: str) -> bytes:
    """Generate PDF bytes from HTML string using WeasyPrint.

    Args:
        html: HTML content string.

    Returns:
        PDF file bytes.

    Raises:
        RuntimeError: If WeasyPrint is not installed or available.
    """
    if HTML is None:
        raise RuntimeError("WeasyPrint is not installed or not available in this environment")
    pdf = HTML(string=html).write_pdf()
    return pdf



def build_invoice_context(
    invoice: Any,
    client: Any,
    project: Any | None,
    line_items: list[Any],
    company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build template context from ORM objects and metadata.
    
    Args:
        invoice: Invoice model instance.
        client: Client model instance.
        project: Project model instance (optional).
        line_items: List of InvoiceLineItem model instances.
        company: Company information dictionary (optional).
    
    Returns:
        Dictionary with template context.
    """
    company = company or {
        "name": "BillOps",
        "email": "billing@example.com",
        "address": "123 Main St, City, Country",
    }

    subtotal_cents = sum(getattr(li, "amount_cents", 0) for li in line_items)
    tax_cents = getattr(invoice, "tax_cents", 0) or 0
    total_cents = subtotal_cents + tax_cents

    # Basic line-item mapping for template
    items = [
        {
            "description": getattr(li, "description", ""),
            "quantity": getattr(li, "quantity", "1"),
            "unit_price_cents": getattr(li, "unit_price_cents", 0),
            "amount_cents": getattr(li, "amount_cents", 0),
        }
        for li in line_items
    ]

    ctx = {
        "company": company,
        "client": {
            "name": getattr(client, "name", "Client"),
            "contact_email": getattr(client, "contact_email", None),
        },
        "project": {"name": getattr(project, "name", None)} if project else None,
        "invoice": {
            "number": getattr(invoice, "invoice_number", "INV-XXXX"),
            "currency": getattr(invoice, "currency", "USD"),
            "issue_date": getattr(invoice, "issue_date", datetime.utcnow()),
            "due_date": getattr(invoice, "due_date", None),
            "notes": getattr(invoice, "notes", None),
        },
        "items": items,
        "subtotal_cents": subtotal_cents,
        "tax_cents": tax_cents,
        "total_cents": total_cents,
    }
    return ctx


def generate_invoice_pdf(
    invoice: Any,
    client: Any,
    project: Any | None,
    line_items: list[Any],
    company: dict[str, Any] | None = None,
    layout: str = DEFAULT_LAYOUT,
) -> bytes:
    """Render invoice HTML and return PDF bytes.
    
    Args:
        invoice: Invoice model instance.
        client: Client model instance.
        project: Project model instance (optional).
        line_items: List of InvoiceLineItem model instances.
        company: Company information dictionary (optional).
        layout: Template layout ('minimalist', 'professional', or 'branded').
                Defaults to 'professional'.
    
    Returns:
        PDF file bytes.
    """
    ctx = build_invoice_context(invoice, client, project, line_items, company)
    html = render_invoice_html(ctx, layout=layout)
    return generate_pdf_from_html(html)
