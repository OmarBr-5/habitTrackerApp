"""Repositories for database access and CRUD operations.

This module implements the repository pattern for data access in the Habit Tracker
application. Repositories provide an abstraction layer between the business logic
and the database, encapsulating all data access operations and providing a clean
API for working with Habit and Completion entities.

Key responsibilities:
- Data persistence and retrieval for habits and completions
- Entity mapping between ORM and domain models
- Database transaction management
- Error handling and validation
- Habit filtering by periodicity
"""

from datetime import datetime
from typing import List, Optional, Union

from sqlalchemy.orm import Session

from models.models import Habit, Completion
from database.database import HabitORM, CompletionORM
from exceptions.exceptions import (
    HabitNotFoundError,
    DuplicateCompletionError,
    DatabaseError,
)


class HabitRepository:
    """Repository for managing Habit CRUD operations.

    This repository provides data access operations for Habit entities, including
    creation, retrieval, updating, and deletion. It handles the mapping between
    the domain model (Habit) and the ORM model (HabitORM).

    The repository supports:
    - Creating new habits with auto-generated IDs
    - Fetching habits by ID or filtering by periodicity
    - Deleting habits with cascade deletion of completions
    - Retrieving all habits from the database

    Attributes:
        session: SQLAlchemy database session for database operations
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy database session for database operations
        """
        self.session = session

    def save_habit(self, habit: Habit) -> Habit:
        """Save a new habit to the database.

        Creates a new habit record in the database. If the habit has an ID of None,
        the database will auto-generate a sequential ID. The method returns the
        saved habit with the database-assigned ID.

        Args:
            habit: Habit data class to save (ID can be None for auto-generation)

        Returns:
            The saved Habit object with database-assigned ID

        Raises:
            DatabaseError: If the save operation fails due to database constraints
                          or connection issues
        """
        try:
            # For new habits, let the database generate the ID
            habit_orm = HabitORM(
                habit_id=(
                    habit.habit_id if habit.habit_id else None
                ),  # Will be auto-generated if None
                habit_name=habit.habit_name,
                periodicity=habit.periodicity,
                created_at=habit.created_at,
            )
            self.session.add(habit_orm)
            self.session.commit()
            return self._orm_to_data(habit_orm)
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to save habit: {str(e)}")

    def delete_habit(self, habit_id: int) -> None:
        """Delete a habit by ID.

        Removes the habit with the specified ID from the database. Due to the
        CASCADE delete relationship, all associated completion records will also
        be automatically deleted.

        Args:
            habit_id: ID of habit to delete

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
            DatabaseError: If the delete operation fails due to database constraints
                          or connection issues
        """
        try:
            habit_orm = (
                self.session.query(HabitORM)
                .filter(HabitORM.habit_id == habit_id)
                .first()
            )

            if not habit_orm:
                raise HabitNotFoundError(habit_id)

            self.session.delete(habit_orm)
            self.session.commit()
        except HabitNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete habit: {str(e)}")

    def fetch_by_id(self, habit_id: int) -> Habit:
        """Fetch a habit by ID.

        Retrieves a single habit from the database using its unique identifier.
        Returns the habit as a domain model object.

        Args:
            habit_id: ID of habit to fetch

        Returns:
            The Habit data object with the specified ID

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
        """
        habit_orm = (
            self.session.query(HabitORM).filter(HabitORM.habit_id == habit_id).first()
        )

        if not habit_orm:
            raise HabitNotFoundError(habit_id)

        return self._orm_to_data(habit_orm)

    def fetch_all(self) -> List[Habit]:
        """Fetch all habits from the database.

        Retrieves all habit records from the database and returns them as a list
        of domain model objects. This method performs a simple SELECT * operation.

        Returns:
            List of all Habit data objects in the database
        """
        habit_orms = self.session.query(HabitORM).all()
        return [self._orm_to_data(orm) for orm in habit_orms]

    def fetch_by_periodicity(self, periodicity: str) -> List[Habit]:
        """Fetch habits filtered by periodicity.

        Retrieves all habits that match the specified periodicity. This is useful
        for displaying habits grouped by their frequency (daily vs weekly).

        Args:
            periodicity: Period to filter by ('Daily' or 'Weekly')

        Returns:
            List of Habit data objects that match the specified periodicity
        """
        habit_orms = (
            self.session.query(HabitORM)
            .filter(HabitORM.periodicity == periodicity)
            .all()
        )
        return [self._orm_to_data(orm) for orm in habit_orms]

    @staticmethod
    def _orm_to_data(habit_orm: HabitORM) -> Habit:
        """Convert ORM model to data class.

        Maps a SQLAlchemy ORM object to the corresponding domain model object.
        This method handles the transformation from database representation to
        application representation.

        Args:
            habit_orm: SQLAlchemy ORM object representing a habit

        Returns:
            Habit domain model object with the same data
        """
        return Habit(
            habit_id=habit_orm.habit_id,
            habit_name=habit_orm.habit_name,
            periodicity=habit_orm.periodicity,
            created_at=habit_orm.created_at,
        )


class CompletionRepository:
    """Repository for managing Completion CRUD operations.

    This repository provides data access operations for Completion entities, including
    creation, retrieval, and validation. It handles the mapping between the domain
    model (Completion) and the ORM model (CompletionORM), and enforces business rules
    such as preventing duplicate completions on the same day.

    Attributes:
        session: SQLAlchemy database session for database operations
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy database session for database operations
        """
        self.session = session

    def save_completion(self, completion: Completion) -> Completion:
        """Save a new completion record to the database.

        Creates a new completion record for a habit. Before saving, the method
        validates that the associated habit exists and that no duplicate completion
        exists for the same habit on the same date.

        Args:
            completion: Completion data class to save (ID can be None for auto-generation)

        Returns:
            The saved Completion object with database-assigned ID

        Raises:
            HabitNotFoundError: If the associated habit doesn't exist
            DuplicateCompletionError: If a completion already exists for this habit on the same date
            DatabaseError: If the save operation fails due to database constraints or connection issues
        """
        try:
            # Verify habit exists
            habit_exists = (
                self.session.query(HabitORM)
                .filter(HabitORM.habit_id == completion.habit_id)
                .first()
            )

            if not habit_exists:
                raise HabitNotFoundError(completion.habit_id)

            # Check for duplicate completion on the same date
            completion_date = completion.date_of_completion.date()
            existing = (
                self.session.query(CompletionORM)
                .filter(
                    CompletionORM.habit_id == completion.habit_id,
                    CompletionORM.date_of_completion
                    >= datetime.combine(
                        completion_date, __import__("datetime").time.min
                    ),
                    CompletionORM.date_of_completion
                    < datetime.combine(
                        completion_date, __import__("datetime").time.max
                    ),
                )
                .first()
            )

            if existing:
                raise DuplicateCompletionError(
                    completion.habit_id, completion_date.isoformat()
                )

            completion_orm = CompletionORM(
                completion_id=(
                    completion.completion_id if completion.completion_id else None
                ),  # Will be auto-generated if None
                habit_id=completion.habit_id,
                date_of_completion=completion.date_of_completion,
            )
            self.session.add(completion_orm)
            self.session.commit()
            return self._orm_to_data(completion_orm)
        except (HabitNotFoundError, DuplicateCompletionError):
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to save completion: {str(e)}")

    def fetch_completions(self, habit_id: int) -> List[Completion]:
        """Fetch all completions for a specific habit.

        Retrieves all completion records associated with the specified habit,
        sorted by completion date in ascending order. This is useful for
        analyzing completion patterns and calculating streaks.

        Args:
            habit_id: ID of the habit to fetch completions for

        Returns:
            List of Completion data objects for the specified habit, sorted by date

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
        """
        # Verify habit exists
        habit_exists = (
            self.session.query(HabitORM).filter(HabitORM.habit_id == habit_id).first()
        )

        if not habit_exists:
            raise HabitNotFoundError(habit_id)

        completion_orms = (
            self.session.query(CompletionORM)
            .filter(CompletionORM.habit_id == habit_id)
            .order_by(CompletionORM.date_of_completion)
            .all()
        )

        return [self._orm_to_data(orm) for orm in completion_orms]

    @staticmethod
    def _orm_to_data(completion_orm: CompletionORM) -> Completion:
        """Convert ORM model to data class.

        Maps a SQLAlchemy ORM object to the corresponding domain model object.
        This method handles the transformation from database representation to
        application representation.

        Args:
            completion_orm: SQLAlchemy ORM object representing a completion

        Returns:
            Completion domain model object with the same data
        """
        return Completion(
            completion_id=completion_orm.completion_id,
            habit_id=completion_orm.habit_id,
            date_of_completion=completion_orm.date_of_completion,
        )
