from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.services.invoice import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=dict[str, object])
def list_invoices(
    client_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """List invoices with optional filtering and pagination."""
    if client_id:
        invoices = InvoiceService.get_by_client(db, client_id, skip=skip, limit=limit)
        total = InvoiceService.count_by_client(db, client_id)
    elif status_filter:
        invoices = InvoiceService.get_by_status(db, status_filter, skip=skip, limit=limit)
        total = len(invoices)
    else:
        invoices = InvoiceService.get_all(db, skip=skip, limit=limit)
        total = len(invoices)
    return {
        "items": invoices,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    """Create a new invoice."""
    invoice = InvoiceService.create(db, data)
    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    """Get an invoice by ID."""
    invoice = InvoiceService.get_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return InvoiceResponse.model_validate(invoice)


@router.get("/number/{invoice_number}", response_model=InvoiceResponse)
def get_invoice_by_number(
    invoice_number: str,
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    """Get an invoice by invoice number."""
    invoice = InvoiceService.get_by_number(db, invoice_number)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: UUID,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    """Update an invoice."""
    invoice = InvoiceService.update(db, invoice_id, data)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an invoice."""
    success = InvoiceService.delete(db, invoice_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
