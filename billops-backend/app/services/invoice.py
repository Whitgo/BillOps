"""CRUD service for Invoice model."""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Service for Invoice CRUD operations."""

    @staticmethod
    def create(db: Session, invoice_data: InvoiceCreate) -> Invoice:
        """
        Create a new invoice.
        
        Args:
            db: Database session.
            invoice_data: Invoice creation data.
            
        Returns:
            The created invoice.
        """
        db_invoice = Invoice(**invoice_data.model_dump())
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    @staticmethod
    def get_by_id(db: Session, invoice_id: UUID) -> Invoice | None:
        """Get an invoice by ID."""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()

    @staticmethod
    def get_by_number(db: Session, invoice_number: str) -> Invoice | None:
        """Get an invoice by invoice number."""
        return db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()

    @staticmethod
    def get_by_client(db: Session, client_id: UUID, skip: int = 0, limit: int = 50) -> list[Invoice]:
        """Get all invoices for a client."""
        return db.query(Invoice).filter(
            Invoice.client_id == client_id
        ).offset(skip).limit(limit).order_by(Invoice.issue_date.desc()).all()

    @staticmethod
    def get_by_status(db: Session, status: str, skip: int = 0, limit: int = 50) -> list[Invoice]:
        """Get all invoices with a specific status."""
        return db.query(Invoice).filter(
            Invoice.status == status
        ).offset(skip).limit(limit).order_by(Invoice.issue_date.desc()).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Invoice]:
        """Get all invoices with pagination."""
        return db.query(Invoice).offset(skip).limit(limit).order_by(Invoice.issue_date.desc()).all()

    @staticmethod
    def update(db: Session, invoice_id: UUID, invoice_data: InvoiceUpdate) -> Invoice | None:
        """
        Update an invoice.
        
        Args:
            db: Database session.
            invoice_id: ID of invoice to update.
            invoice_data: Updated invoice data.
            
        Returns:
            The updated invoice, or None if not found.
        """
        db_invoice = InvoiceService.get_by_id(db, invoice_id)
        if not db_invoice:
            return None

        update_data = invoice_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_invoice, key, value)

        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    @staticmethod
    def delete(db: Session, invoice_id: UUID) -> bool:
        """
        Delete an invoice.
        
        Args:
            db: Database session.
            invoice_id: ID of invoice to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        db_invoice = InvoiceService.get_by_id(db, invoice_id)
        if not db_invoice:
            return False

        db.delete(db_invoice)
        db.commit()
        return True

    @staticmethod
    def count_by_client(db: Session, client_id: UUID) -> int:
        """Get number of invoices for a client."""
        return db.query(Invoice).filter(Invoice.client_id == client_id).count()

    @staticmethod
    def total_revenue(db: Session, client_id: UUID) -> int:
        """Get total revenue (in cents) from all invoices for a client."""
        result = db.query(func.sum(Invoice.total_cents)).filter(
            Invoice.client_id == client_id,
            Invoice.status == "paid",
        ).scalar()
        return result or 0

    @staticmethod
    def outstanding_amount(db: Session, client_id: UUID) -> int:
        """Get outstanding amount (in cents) for a client."""
        result = db.query(func.sum(Invoice.total_cents)).filter(
            Invoice.client_id == client_id,
            Invoice.status.in_(["draft", "sent", "partial", "overdue"]),
        ).scalar()
        return result or 0

    @staticmethod
    def get_total_paid(db: Session, invoice_id: UUID) -> int:
        """Get total amount paid (in cents) against an invoice."""
        result = db.query(func.sum(Payment.amount_cents)).filter(
            Payment.invoice_id == invoice_id,
        ).scalar()
        return result or 0
