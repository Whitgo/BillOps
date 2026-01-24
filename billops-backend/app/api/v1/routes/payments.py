from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services.payment import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/", response_model=dict[str, object])
def list_payments(
    invoice_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """List payments with optional invoice filtering and pagination."""
    if invoice_id:
        payments = PaymentService.get_by_invoice(db, invoice_id, skip=skip, limit=limit)
        total = PaymentService.count_by_invoice(db, invoice_id)
    else:
        payments = PaymentService.get_all(db, skip=skip, limit=limit)
        total = len(payments)
    return {
        "items": payments,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Create a new payment."""
    payment = PaymentService.create(db, data)
    return PaymentResponse.model_validate(payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Get a payment by ID."""
    payment = PaymentService.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return PaymentResponse.model_validate(payment)


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: UUID,
    data: PaymentUpdate,
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Update a payment."""
    payment = PaymentService.update(db, payment_id, data)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return PaymentResponse.model_validate(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a payment."""
    success = PaymentService.delete(db, payment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
