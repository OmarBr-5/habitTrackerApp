"""Business logic services."""

from datetime import datetime, timedelta, date
from typing import List, Optional

from sqlalchemy.orm import Session

from models.models import Habit, Completion
from repositories.repositories import HabitRepository, CompletionRepository
from exceptions.exceptions import (
    InvalidPeriodicityError,
    InvalidHabitError,
    HabitNotFoundError,
)


class HabitService:
    """Service for managing habit business logic and operations."""
    
    VALID_PERIODICITIES = {"Daily", "Weekly"}
    
    def __init__(self, session: Session):
        """Initialize service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.habit_repo = HabitRepository(session)
        self.completion_repo = CompletionRepository(session)
    
    def init_predefined_habits(self) -> List[Habit]:
        """Create five predefined habits in the database.

        Returns:
            List of created Habit objects
        """
        predefined = [
            ("Wake up early", "Daily"),
            ("Read 10 pages", "Daily"),
            ("Exercise", "Daily"),
            ("Meditation", "Daily"),
            ("Weekly review", "Weekly"),
        ]

        created_habits = []
        for name, periodicity in predefined:
            habit = Habit(
                habit_id=None,  # Let database auto-generate sequential ID
                habit_name=name,
                periodicity=periodicity,
                created_at=datetime.now(),
            )
            saved = self.habit_repo.save_habit(habit)
            created_habits.append(saved)

        return created_habits
    
    def add_habit(self, habit_name: str, periodicity: str) -> Habit:
        """Add a new habit.

        Args:
            habit_name: Name of the habit
            periodicity: How often the habit occurs ('Daily' or 'Weekly')

        Returns:
            The created Habit object

        Raises:
            InvalidPeriodicityError: If periodicity is invalid
            InvalidHabitError: If habit name is empty
        """
        if not habit_name or not habit_name.strip():
            raise InvalidHabitError("Habit name cannot be empty")

        if periodicity not in self.VALID_PERIODICITIES:
            raise InvalidPeriodicityError(periodicity)

        habit = Habit(
            habit_id=None,  # Let database auto-generate sequential ID
            habit_name=habit_name.strip(),
            periodicity=periodicity,
            created_at=datetime.now(),
        )

        return self.habit_repo.save_habit(habit)
    
    def remove_habit(self, habit_id: int) -> None:
        """Remove a habit by ID.

        Args:
            habit_id: ID of habit to remove

        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        self.habit_repo.delete_habit(habit_id)
    
    def calculate_streak(self, habit_id: int) -> int:
        """Calculate the current consecutive streak for a habit.

        Args:
            habit_id: ID of the habit

        Returns:
            Number of consecutive completed periods

        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        habit = self.habit_repo.fetch_by_id(habit_id)
        completions = self.completion_repo.fetch_completions(habit_id)
        
        if not completions:
            return 0
        
        # Convert completion dates to date objects and sort
        dates = sorted([comp.date_of_completion.date() for comp in completions])
        
        # Calculate streak based on periodicity
        if habit.periodicity == "Daily":
            return self._calculate_daily_streak(dates)
        elif habit.periodicity == "Weekly":
            return self._calculate_weekly_streak(dates)
        
        return 0
    
    def is_broken(self, habit_id: int) -> bool:
        """Check if a habit's streak is broken.

        Args:
            habit_id: ID of the habit

        Returns:
            True if streak is broken, False if active or no history

        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        habit = self.habit_repo.fetch_by_id(habit_id)
        completions = self.completion_repo.fetch_completions(habit_id)
        
        if not completions:
            return False
        
        dates = sorted([comp.date_of_completion.date() for comp in completions])
        today = date.today()
        last_completion = dates[-1]
        
        if habit.periodicity == "Daily":
            # For daily habits, broken if last completion is more than 1 day ago
            return (today - last_completion).days > 1
        elif habit.periodicity == "Weekly":
            # For weekly habits, broken if last completion is more than 7 days ago
            return (today - last_completion).days > 7
        
        return False
    
    @staticmethod
    def _calculate_daily_streak(dates: List[date]) -> int:
        """Calculate consecutive daily streak.
        
        Args:
            dates: Sorted list of completion dates
            
        Returns:
            Length of current streak
        """
        if not dates:
            return 0
        
        today = date.today()
        streak = 0
        current_date = today
        
        # Iterate backwards from today
        for completion_date in reversed(dates):
            if completion_date == current_date or completion_date == current_date - timedelta(days=1):
                streak += 1
                current_date = completion_date
            else:
                break
        
        return streak
    
    @staticmethod
    def _calculate_weekly_streak(dates: List[date]) -> int:
        """Calculate consecutive weekly streak.
        
        Args:
            dates: Sorted list of completion dates
            
        Returns:
            Length of current streak
        """
        if not dates:
            return 0
        
        today = date.today()
        streak = 0
        current_week = today.isocalendar()[1]
        current_year = today.isocalendar()[0]
        
        # Iterate backwards through dates
        for completion_date in reversed(dates):
            comp_week = completion_date.isocalendar()[1]
            comp_year = completion_date.isocalendar()[0]
            
            if (comp_year == current_year and comp_week == current_week) or \
               (comp_year == current_year and comp_week == current_week - 1):
                streak += 1
                current_week -= 1
            else:
                break
        
        return streak


class CompletionService:
    """Service for managing habit completions."""
    
    def __init__(self, session: Session):
        """Initialize service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.completion_repo = CompletionRepository(session)
        self.habit_repo = HabitRepository(session)
    
    def mark_habit_as_completed(
        self,
        habit_id: int,
        completion_date: Optional[datetime] = None,
    ) -> Completion:
        """Mark a habit as completed.

        Creates a completion record for the specified habit.

        Args:
            habit_id: ID of the habit to complete
            completion_date: Date of completion (defaults to today)

        Returns:
            The created Completion object

        Raises:
            HabitNotFoundError: If habit doesn't exist
            DuplicateCompletionError: If already completed today
        """
        # Verify habit exists
        self.habit_repo.fetch_by_id(habit_id)

        completion = Completion(
            completion_id=None,  # Let database auto-generate sequential ID
            habit_id=habit_id,
            date_of_completion=completion_date or datetime.now(),
        )

        return self.completion_repo.save_completion(completion)
