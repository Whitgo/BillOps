from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.billing_rule import BillingRuleCreate, BillingRuleResponse, BillingRuleUpdate
from app.services.billing_rule import BillingRuleService

router = APIRouter(prefix="/billing-rules", tags=["billing_rules"])


@router.get("/", response_model=dict[str, object])
def list_billing_rules(
    project_id: UUID | None = Query(None),
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """List billing rules with optional project filtering and pagination."""
    if project_id:
        if active_only:
            rules = BillingRuleService.get_active_for_project(db, project_id)
        else:
            rules = BillingRuleService.get_by_project(db, project_id, skip=skip, limit=limit)
        total = BillingRuleService.count_by_project(db, project_id)
    else:
        rules = BillingRuleService.get_all(db, skip=skip, limit=limit)
        total = len(rules)
    return {
        "items": rules,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", response_model=BillingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_billing_rule(
    data: BillingRuleCreate,
    db: Session = Depends(get_db),
) -> BillingRuleResponse:
    """Create a new billing rule."""
    rule = BillingRuleService.create(db, data)
    return BillingRuleResponse.model_validate(rule)


@router.get("/{rule_id}", response_model=BillingRuleResponse)
def get_billing_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
) -> BillingRuleResponse:
    """Get a billing rule by ID."""
    rule = BillingRuleService.get_by_id(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing rule not found",
        )
    return BillingRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=BillingRuleResponse)
def update_billing_rule(
    rule_id: UUID,
    data: BillingRuleUpdate,
    db: Session = Depends(get_db),
) -> BillingRuleResponse:
    """Update a billing rule."""
    rule = BillingRuleService.update(db, rule_id, data)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing rule not found",
        )
    return BillingRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_billing_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a billing rule."""
    success = BillingRuleService.delete(db, rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing rule not found",
        )
