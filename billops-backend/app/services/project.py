"""CRUD service for Project model."""
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for Project CRUD operations."""

    @staticmethod
    def create(db: Session, project_data: ProjectCreate, user_id: UUID) -> Project:
        """
        Create a new project.
        
        Args:
            db: Database session.
            project_data: Project creation data.
            user_id: ID of user creating the project.
            
        Returns:
            The created project.
        """
        db_project = Project(
            **project_data.model_dump(),
            created_by=user_id,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_by_id(db: Session, project_id: UUID) -> Project | None:
        """Get a project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_by_client(db: Session, client_id: UUID, skip: int = 0, limit: int = 50) -> list[Project]:
        """Get all projects for a client."""
        return db.query(Project).filter(
            Project.client_id == client_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Project]:
        """Get all projects with pagination."""
        return db.query(Project).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, project_id: UUID, project_data: ProjectUpdate) -> Project | None:
        """
        Update a project.
        
        Args:
            db: Database session.
            project_id: ID of project to update.
            project_data: Updated project data.
            
        Returns:
            The updated project, or None if not found.
        """
        db_project = ProjectService.get_by_id(db, project_id)
        if not db_project:
            return None

        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def delete(db: Session, project_id: UUID) -> bool:
        """
        Delete a project.
        
        Args:
            db: Database session.
            project_id: ID of project to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        db_project = ProjectService.get_by_id(db, project_id)
        if not db_project:
            return False

        db.delete(db_project)
        db.commit()
        return True

    @staticmethod
    def count_by_client(db: Session, client_id: UUID) -> int:
        """Get number of projects for a client."""
        return db.query(Project).filter(Project.client_id == client_id).count()
