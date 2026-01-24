"""CRUD service for BillingRule model."""
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.billing_rule import BillingRule
from app.schemas.billing_rule import BillingRuleCreate, BillingRuleUpdate


class BillingRuleService:
    """Service for BillingRule CRUD operations."""

    @staticmethod
    def create(db: Session, rule_data: BillingRuleCreate) -> BillingRule:
        """
        Create a new billing rule.
        
        Args:
            db: Database session.
            rule_data: Billing rule creation data.
            
        Returns:
            The created billing rule.
        """
        db_rule = BillingRule(**rule_data.model_dump())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule

    @staticmethod
    def get_by_id(db: Session, rule_id: UUID) -> BillingRule | None:
        """Get a billing rule by ID."""
        return db.query(BillingRule).filter(BillingRule.id == rule_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: UUID, skip: int = 0, limit: int = 50) -> list[BillingRule]:
        """Get all billing rules for a project."""
        return db.query(BillingRule).filter(
            BillingRule.project_id == project_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_active_for_project(db: Session, project_id: UUID) -> BillingRule | None:
        """Get the active billing rule for a project (most recent effective_from)."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        return db.query(BillingRule).filter(
            BillingRule.project_id == project_id,
            BillingRule.effective_from <= now,
            (BillingRule.effective_to == None) | (BillingRule.effective_to > now),
        ).order_by(BillingRule.effective_from.desc()).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[BillingRule]:
        """Get all billing rules with pagination."""
        return db.query(BillingRule).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, rule_id: UUID, rule_data: BillingRuleUpdate) -> BillingRule | None:
        """
        Update a billing rule.
        
        Args:
            db: Database session.
            rule_id: ID of rule to update.
            rule_data: Updated rule data.
            
        Returns:
            The updated rule, or None if not found.
        """
        db_rule = BillingRuleService.get_by_id(db, rule_id)
        if not db_rule:
            return None

        update_data = rule_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_rule, key, value)

        db.commit()
        db.refresh(db_rule)
        return db_rule

    @staticmethod
    def delete(db: Session, rule_id: UUID) -> bool:
        """
        Delete a billing rule.
        
        Args:
            db: Database session.
            rule_id: ID of rule to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        db_rule = BillingRuleService.get_by_id(db, rule_id)
        if not db_rule:
            return False

        db.delete(db_rule)
        db.commit()
        return True

    @staticmethod
    def count_by_project(db: Session, project_id: UUID) -> int:
        """Get number of billing rules for a project."""
        return db.query(BillingRule).filter(BillingRule.project_id == project_id).count()
