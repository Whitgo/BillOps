"""CRUD service for Client model."""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    """Service for Client CRUD operations."""

    @staticmethod
    def create(db: Session, client_data: ClientCreate, user_id: UUID) -> Client:
        """
        Create a new client.
        
        Args:
            db: Database session.
            client_data: Client creation data.
            user_id: ID of user creating the client.
            
        Returns:
            The created client.
        """
        db_client = Client(
            **client_data.model_dump(),
            created_by=user_id,
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def get_by_id(db: Session, client_id: UUID) -> Client | None:
        """Get a client by ID."""
        return db.query(Client).filter(Client.id == client_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Client]:
        """Get all clients with pagination."""
        return db.query(Client).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, client_id: UUID, client_data: ClientUpdate) -> Client | None:
        """
        Update a client.
        
        Args:
            db: Database session.
            client_id: ID of client to update.
            client_data: Updated client data.
            
        Returns:
            The updated client, or None if not found.
        """
        db_client = ClientService.get_by_id(db, client_id)
        if not db_client:
            return None

        update_data = client_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_client, key, value)

        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def delete(db: Session, client_id: UUID) -> bool:
        """
        Delete a client.
        
        Args:
            db: Database session.
            client_id: ID of client to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        db_client = ClientService.get_by_id(db, client_id)
        if not db_client:
            return False

        db.delete(db_client)
        db.commit()
        return True

    @staticmethod
    def count(db: Session) -> int:
        """Get total number of clients."""
        return db.query(Client).count()
