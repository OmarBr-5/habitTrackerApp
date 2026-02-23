"""Repositories for database access and CRUD operations."""

from datetime import datetime
from typing import List, Optional, Union

from sqlalchemy.orm import Session

from models.models import Habit, Completion
from database.database import HabitORM, CompletionORM
from exceptions.exceptions import (
    HabitNotFoundError,
    CompletionNotFoundError,
    DuplicateCompletionError,
    DatabaseError,
)


class HabitRepository:
    """Repository for managing Habit CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def save_habit(self, habit: Habit) -> Habit:
        """Save a new habit to the database.

        Args:
            habit: Habit data class to save

        Returns:
            The saved Habit with database-assigned ID

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            # For new habits, let the database generate the ID
            habit_orm = HabitORM(
                habit_id=habit.habit_id if habit.habit_id else None,  # Will be auto-generated if None
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

        Args:
            habit_id: ID of habit to delete

        Raises:
            HabitNotFoundError: If habit doesn't exist
            DatabaseError: If delete operation fails
        """
        try:
            habit_orm = self.session.query(HabitORM).filter(
                HabitORM.habit_id == habit_id
            ).first()
            
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

        Args:
            habit_id: ID of habit to fetch

        Returns:
            The Habit data object

        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        habit_orm = self.session.query(HabitORM).filter(
            HabitORM.habit_id == habit_id
        ).first()
        
        if not habit_orm:
            raise HabitNotFoundError(habit_id)
        
        return self._orm_to_data(habit_orm)
    
    def fetch_all(self) -> List[Habit]:
        """Fetch all habits from the database.
        
        Returns:
            List of all Habit data objects
        """
        habit_orms = self.session.query(HabitORM).all()
        return [self._orm_to_data(orm) for orm in habit_orms]
    
    def fetch_by_periodicity(self, periodicity: str) -> List[Habit]:
        """Fetch habits filtered by periodicity.
        
        Args:
            periodicity: Period to filter by ('Daily' or 'Weekly')
            
        Returns:
            List of Habit data objects matching the periodicity
        """
        habit_orms = self.session.query(HabitORM).filter(
            HabitORM.periodicity == periodicity
        ).all()
        return [self._orm_to_data(orm) for orm in habit_orms]
    
    def count_habits(self) -> int:
        """Count total number of habits.
        
        Returns:
            Total count of habits in database
        """
        return self.session.query(HabitORM).count()
    
    def fetch_all_habits_with_completions(self) -> List[tuple[Habit, List[Completion]]]:
        """Fetch all habits with their associated completions.
        
        Returns:
            List of tuples containing (Habit, list of Completion objects)
        """
        habit_orms = self.session.query(HabitORM).all()
        result = []
        
        for habit_orm in habit_orms:
            habit = self._orm_to_data(habit_orm)
            completions = [
                self._completion_orm_to_data(comp) 
                for comp in habit_orm.completions
            ]
            result.append((habit, completions))
        
        return result
    
    @staticmethod
    def _orm_to_data(habit_orm: HabitORM) -> Habit:
        """Convert ORM model to data class."""
        return Habit(
            habit_id=habit_orm.habit_id,
            habit_name=habit_orm.habit_name,
            periodicity=habit_orm.periodicity,
            created_at=habit_orm.created_at,
        )
    
    @staticmethod
    def _completion_orm_to_data(completion_orm: CompletionORM) -> Completion:
        """Convert Completion ORM model to data class."""
        return Completion(
            completion_id=completion_orm.completion_id,
            habit_id=completion_orm.habit_id,
            date_of_completion=completion_orm.date_of_completion,
        )


class CompletionRepository:
    """Repository for managing Completion CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def save_completion(self, completion: Completion) -> Completion:
        """Save a new completion record to the database.
        
        Args:
            completion: Completion data class to save
            
        Returns:
            The saved Completion with database-assigned ID
            
        Raises:
            HabitNotFoundError: If associated habit doesn't exist
            DuplicateCompletionError: If completion already exists for this date
            DatabaseError: If save operation fails
        """
        try:
            # Verify habit exists
            habit_exists = self.session.query(HabitORM).filter(
                HabitORM.habit_id == completion.habit_id
            ).first()
            
            if not habit_exists:
                raise HabitNotFoundError(completion.habit_id)
            
            # Check for duplicate completion on the same date
            completion_date = completion.date_of_completion.date()
            existing = self.session.query(CompletionORM).filter(
                CompletionORM.habit_id == completion.habit_id,
                CompletionORM.date_of_completion >= datetime.combine(completion_date, __import__('datetime').time.min),
                CompletionORM.date_of_completion < datetime.combine(completion_date, __import__('datetime').time.max),
            ).first()
            
            if existing:
                raise DuplicateCompletionError(
                    completion.habit_id, 
                    completion_date.isoformat()
                )
            
            completion_orm = CompletionORM(
                completion_id=completion.completion_id if completion.completion_id else None,  # Will be auto-generated if None
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

        Args:
            habit_id: ID of the habit

        Returns:
            List of Completion data objects for the habit

        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        # Verify habit exists
        habit_exists = self.session.query(HabitORM).filter(
            HabitORM.habit_id == habit_id
        ).first()
        
        if not habit_exists:
            raise HabitNotFoundError(habit_id)
        
        completion_orms = self.session.query(CompletionORM).filter(
            CompletionORM.habit_id == habit_id
        ).order_by(CompletionORM.date_of_completion).all()
        
        return [self._orm_to_data(orm) for orm in completion_orms]
    
    @staticmethod
    def _orm_to_data(completion_orm: CompletionORM) -> Completion:
        """Convert ORM model to data class."""
        return Completion(
            completion_id=completion_orm.completion_id,
            habit_id=completion_orm.habit_id,
            date_of_completion=completion_orm.date_of_completion,
        )
