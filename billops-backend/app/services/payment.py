"""CRUD service for Payment model."""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentService:
    """Service for Payment CRUD operations."""

    @staticmethod
    def create(db: Session, payment_data: PaymentCreate) -> Payment:
        """
        Create a new payment.
        
        Args:
            db: Database session.
            payment_data: Payment creation data.
            
        Returns:
            The created payment.
        """
        db_payment = Payment(**payment_data.model_dump())
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def get_by_id(db: Session, payment_id: UUID) -> Payment | None:
        """Get a payment by ID."""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def get_by_invoice(db: Session, invoice_id: UUID, skip: int = 0, limit: int = 50) -> list[Payment]:
        """Get all payments for an invoice."""
        return db.query(Payment).filter(
            Payment.invoice_id == invoice_id
        ).offset(skip).limit(limit).order_by(Payment.received_at.desc()).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Payment]:
        """Get all payments with pagination."""
        return db.query(Payment).offset(skip).limit(limit).order_by(Payment.received_at.desc()).all()

    @staticmethod
    def update(db: Session, payment_id: UUID, payment_data: PaymentUpdate) -> Payment | None:
        """
        Update a payment.
        
        Args:
            db: Database session.
            payment_id: ID of payment to update.
            payment_data: Updated payment data.
            
        Returns:
            The updated payment, or None if not found.
        """
        db_payment = PaymentService.get_by_id(db, payment_id)
        if not db_payment:
            return None

        update_data = payment_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_payment, key, value)

        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def delete(db: Session, payment_id: UUID) -> bool:
        """
        Delete a payment.
        
        Args:
            db: Database session.
            payment_id: ID of payment to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        db_payment = PaymentService.get_by_id(db, payment_id)
        if not db_payment:
            return False

        db.delete(db_payment)
        db.commit()
        return True

    @staticmethod
    def count_by_invoice(db: Session, invoice_id: UUID) -> int:
        """Get number of payments for an invoice."""
        return db.query(Payment).filter(Payment.invoice_id == invoice_id).count()

    @staticmethod
    def total_amount_by_invoice(db: Session, invoice_id: UUID) -> int:
        """Get total amount paid (in cents) against an invoice."""
        result = db.query(func.sum(Payment.amount_cents)).filter(
            Payment.invoice_id == invoice_id,
        ).scalar()
        return result or 0

    @staticmethod
    def total_amount_by_method(db: Session, method: str) -> int:
        """Get total amount (in cents) paid using a specific method."""
        result = db.query(func.sum(Payment.amount_cents)).filter(
            Payment.method == method,
        ).scalar()
        return result or 0
