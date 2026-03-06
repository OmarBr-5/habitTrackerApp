"""Business logic services.

This module contains the core business logic services for the Habit Tracker application.
It implements the service layer that coordinates between the presentation layer (CLI)
and the data access layer (repositories). The services encapsulate the business rules
and provide a clean API for habit management operations.

Key responsibilities:
- Habit creation, deletion, and management
- Completion tracking and validation
- Streak calculation and analysis
- Business rule enforcement and validation
"""

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
    """Service for managing habit business logic and operations.

    This service handles all business logic related to habit management including
    creation, deletion, streak calculation, and validation. It enforces business
    rules and coordinates with the repository layer for data persistence.

    Attributes:
        session: SQLAlchemy database session for data operations
        habit_repo: Repository for habit data access
        completion_repo: Repository for completion data access
        VALID_PERIODICITIES: Set of valid periodicity values
    """

    VALID_PERIODICITIES = {"Daily", "Weekly"}

    def __init__(self, session: Session):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy database session for data operations
        """
        self.session = session
        self.habit_repo = HabitRepository(session)
        self.completion_repo = CompletionRepository(session)

    def init_predefined_habits(self) -> List[Habit]:
        """Create five predefined habits in the database.

        This method creates a set of sample habits to help users get started
        with the application. These habits are only created if the database
        is empty (first-time application launch).

        Predefined habits:
        - Wake up early (Daily)
        - Read 10 pages (Daily)
        - Exercise (Daily)
        - Meditation (Daily)
        - Weekly review (Weekly)

        Returns:
            List of created Habit objects that were saved to the database
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

        Creates a new habit with the specified name and periodicity. The habit
        is validated before creation and saved to the database with a creation
        timestamp.

        Args:
            habit_name: Name of the habit (must not be empty)
            periodicity: How often the habit occurs ('Daily' or 'Weekly')

        Returns:
            The created Habit object with database-assigned ID

        Raises:
            InvalidPeriodicityError: If periodicity is not 'Daily' or 'Weekly'
            InvalidHabitError: If habit name is empty or contains only whitespace
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

        Deletes the habit with the specified ID from the database. This operation
        also cascades to delete all associated completion records due to the
        foreign key relationship.

        Args:
            habit_id: ID of habit to remove

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
            DatabaseError: If the deletion operation fails
        """
        self.habit_repo.delete_habit(habit_id)

    def calculate_streak(self, habit_id: int) -> int:
        """Calculate the current consecutive streak for a habit.

        Determines the current active streak by analyzing recent completion
        patterns. For daily habits, it counts consecutive days with completions.
        For weekly habits, it counts consecutive weeks with completions.

        The streak calculation works backwards from today, counting completed
        periods until a gap is found.

        Args:
            habit_id: ID of the habit to calculate streak for

        Returns:
            Number of consecutive completed periods (0 if no completions)

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
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

        Determines if the current streak for a habit has been broken by checking
        the time gap between the last completion and today. A streak is considered
        broken if:
        - For daily habits: Last completion was more than 1 day ago
        - For weekly habits: Last completion was more than 7 days ago

        Args:
            habit_id: ID of the habit to check

        Returns:
            True if the streak is broken, False if active or no completion history

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
        """
        habit = self.habit_repo.fetch_by_id(habit_id)
        completions = self.completion_repo.fetch_completions(habit_id)

        # if there are no recorded completions we still need to know
        # whether the habit has already missed its first expected
        # occurrence; use the creation date as the reference point.
        today = date.today()
        if not completions:
            created = (
                habit.created_at.date()
                if isinstance(habit.created_at, datetime)
                else habit.created_at
            )
            if habit.periodicity == "Daily":
                return (today - created).days > 1
            elif habit.periodicity == "Weekly":
                return (today - created).days > 7
            return False

        dates = sorted([comp.date_of_completion.date() for comp in completions])
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

        Counts the number of consecutive days with completions, working backwards
        from today. A day is considered consecutive if it immediately follows
        the previous completion day.

        Args:
            dates: Sorted list of completion dates (ascending order)

        Returns:
            Length of current consecutive streak in days
        """
        if not dates:
            return 0

        today = date.today()
        streak = 0
        current_date = today

        # Iterate backwards from today
        for completion_date in reversed(dates):
            if (
                completion_date == current_date
                or completion_date == current_date - timedelta(days=1)
            ):
                streak += 1
                current_date = completion_date
            else:
                break

        return streak

    @staticmethod
    def _calculate_weekly_streak(dates: List[date]) -> int:
        """Calculate consecutive weekly streak.

        Counts the number of consecutive weeks with completions, working backwards
        from the current week. A week is considered consecutive if it immediately
        follows the previous completion week in the ISO calendar.

        Args:
            dates: Sorted list of completion dates (ascending order)

        Returns:
            Length of current consecutive streak in weeks
        """
        if not dates:
            return 0

        # Work with unique ISO weeks to avoid double-counting multiple completions
        unique_weeks = sorted(
            {(d.isocalendar()[0], d.isocalendar()[1]) for d in dates}
        )

        def prev_iso_week(year: int, week: int) -> tuple[int, int]:
            prev_monday = date.fromisocalendar(year, week, 1) - timedelta(days=7)
            iso = prev_monday.isocalendar()
            return iso[0], iso[1]

        today_iso = date.today().isocalendar()
        expected_year, expected_week = today_iso[0], today_iso[1]
        streak = 0

        for year, week in reversed(unique_weeks):
            if (year, week) == (expected_year, expected_week):
                streak += 1
                expected_year, expected_week = prev_iso_week(expected_year, expected_week)
                continue

            if streak == 0:
                prev_year, prev_week = prev_iso_week(expected_year, expected_week)
                if (year, week) == (prev_year, prev_week):
                    streak += 1
                    expected_year, expected_week = prev_iso_week(prev_year, prev_week)
                    continue

            break

        return streak


class CompletionService:
    """Service for managing habit completions.

    This service handles the business logic for recording and managing habit
    completions. It validates completions, prevents duplicates, and coordinates
    with the repository layer for data persistence.

    Attributes:
        session: SQLAlchemy database session for data operations
        completion_repo: Repository for completion data access
        habit_repo: Repository for habit data access (for validation)
    """

    def __init__(self, session: Session):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy database session for data operations
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

        Records a completion for the specified habit on the given date. If no
        date is provided, the current date and time are used. The service validates
        that the habit exists and prevents duplicate completions on the same day.

        Args:
            habit_id: ID of the habit to complete
            completion_date: Date and time of completion (defaults to now)

        Returns:
            The created Completion object with database-assigned ID

        Raises:
            HabitNotFoundError: If no habit exists with the given ID
            DuplicateCompletionError: If a completion already exists for this habit on the same day
            DatabaseError: If the save operation fails
        """
        # Verify habit exists
        self.habit_repo.fetch_by_id(habit_id)

        completion = Completion(
            completion_id=None,  # Let database auto-generate sequential ID
            habit_id=habit_id,
            date_of_completion=completion_date or datetime.now(),
        )

        return self.completion_repo.save_completion(completion)
