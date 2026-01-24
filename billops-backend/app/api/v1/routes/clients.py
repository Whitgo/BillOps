from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.services.client import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=dict[str, object])
def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """List all clients with pagination."""
    clients = ClientService.get_all(db, skip=skip, limit=limit)
    total = ClientService.count(db)
    return {
        "items": clients,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
) -> ClientResponse:
    """Create a new client."""
    client = ClientService.create(db, data)
    return ClientResponse.model_validate(client)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
) -> ClientResponse:
    """Get a client by ID."""
    client = ClientService.get_by_id(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return ClientResponse.model_validate(client)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    db: Session = Depends(get_db),
) -> ClientResponse:
    """Update a client."""
    client = ClientService.update(db, client_id, data)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a client."""
    success = ClientService.delete(db, client_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
