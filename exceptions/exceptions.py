"""Custom exception classes for error handling."""

from typing import Union


class HabitTrackerException(Exception):
    """Base exception for all Habit Tracker errors."""

    pass


class HabitNotFoundError(HabitTrackerException):
    """Raised when a habit cannot be found in the database."""

    def __init__(self, habit_id: Union[int, str]):
        super().__init__(f"Habit with ID '{habit_id}' not found.")


class InvalidHabitError(HabitTrackerException):
    """Raised when habit data is invalid."""
    
    def __init__(self, message: str):
        super().__init__(f"Invalid habit data: {message}")


class InvalidPeriodicityError(HabitTrackerException):
    """Raised when an invalid periodicity is provided."""
    
    def __init__(self, periodicity: str):
        super().__init__(
            f"Invalid periodicity '{periodicity}'. Must be 'Daily' or 'Weekly'."
        )


class CompletionNotFoundError(HabitTrackerException):
    """Raised when a completion record cannot be found."""

    def __init__(self, completion_id: str):
        super().__init__(f"Completion with ID '{completion_id}' not found.")


class DuplicateCompletionError(HabitTrackerException):
    """Raised when attempting to create a duplicate completion on the same day."""

    def __init__(self, habit_id: str, date: str):
        super().__init__(
            f"Habit '{habit_id}' already completed on {date}."
        )


class DatabaseError(HabitTrackerException):
    """Raised when a database operation fails."""
    
    def __init__(self, message: str):
        super().__init__(f"Database error: {message}")
