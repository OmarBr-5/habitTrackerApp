"""Custom exception classes for error handling.

This module defines the exception hierarchy for the Habit Tracker application.
All exceptions inherit from HabitTrackerException, providing a consistent
way to handle errors throughout the application.

The exception classes are designed to:
- Provide clear, descriptive error messages
- Support proper error handling and logging
- Enable graceful error recovery where appropriate
- Maintain separation between different types of errors

Exception types:
- Base exceptions for application-wide errors
- Validation exceptions for input validation failures
- Data access exceptions for database operations
- Business logic exceptions for rule violations
"""

from typing import Union


class HabitTrackerException(Exception):
    """Base exception for all Habit Tracker errors.

    This is the base class for all custom exceptions in the Habit Tracker
    application. All other exceptions should inherit from this class to
    enable consistent error handling throughout the application.

    Example:
        try:
            # Some habit tracking operation
            pass
        except HabitTrackerException as e:
            # Handle any habit tracker error
            logger.error(f"Habit tracker error: {e}")
    """

    pass


class HabitNotFoundError(HabitTrackerException):
    """Raised when a habit cannot be found in the database.

    This exception is raised when an operation attempts to access a habit
    that does not exist in the database. This typically occurs when trying
    to perform operations on habits with invalid IDs.

    Attributes:
        habit_id: The ID of the habit that was not found

    Example:
        try:
            habit = habit_service.get_habit(999)
        except HabitNotFoundError as e:
            print(f"Habit not found: {e}")
    """

    def __init__(self, habit_id: Union[int, str]):
        """Initialize the exception with the habit ID.

        Args:
            habit_id: The ID of the habit that was not found (can be int or str)
        """
        super().__init__(f"Habit with ID '{habit_id}' not found.")


class InvalidHabitError(HabitTrackerException):
    """Raised when habit data is invalid.

    This exception is raised when habit creation or modification fails
    due to invalid data, such as empty habit names or other validation
    failures.

    Attributes:
        message: Description of the validation error

    Example:
        try:
            habit = habit_service.add_habit("", "Daily")
        except InvalidHabitError as e:
            print(f"Invalid habit data: {e}")
    """

    def __init__(self, message: str):
        """Initialize the exception with an error message.

        Args:
            message: Description of the validation error
        """
        super().__init__(f"Invalid habit data: {message}")


class InvalidPeriodicityError(HabitTrackerException):
    """Raised when an invalid periodicity is provided.

    This exception is raised when a habit is created or modified with
    an invalid periodicity value. Only 'Daily' and 'Weekly' are valid
    periodicity values.

    Attributes:
        periodicity: The invalid periodicity value that was provided

    Example:
        try:
            habit = habit_service.add_habit("Exercise", "Monthly")
        except InvalidPeriodicityError as e:
            print(f"Invalid periodicity: {e}")
    """

    def __init__(self, periodicity: str):
        """Initialize the exception with the invalid periodicity.

        Args:
            periodicity: The invalid periodicity value that was provided
        """
        super().__init__(
            f"Invalid periodicity '{periodicity}'. Must be 'Daily' or 'Weekly'."
        )


class DuplicateCompletionError(HabitTrackerException):
    """Raised when attempting to create a duplicate completion on the same day.

    This exception is raised when a user tries to mark a habit as completed
    multiple times on the same day. The application prevents duplicate
    completions to maintain data integrity.

    Attributes:
        habit_id: The ID of the habit that was already completed
        date: The date when the duplicate completion was attempted

    Example:
        try:
            completion_service.mark_habit_as_completed(1, datetime.now())
            completion_service.mark_habit_as_completed(1, datetime.now())  # Duplicate
        except DuplicateCompletionError as e:
            print(f"Duplicate completion: {e}")
    """

    def __init__(self, habit_id: str, date: str):
        """Initialize the exception with habit ID and date.

        Args:
            habit_id: The ID of the habit that was already completed
            date: The date when the duplicate completion was attempted
        """
        super().__init__(f"Habit '{habit_id}' already completed on {date}.")


class DatabaseError(HabitTrackerException):
    """Raised when a database operation fails.

    This exception is raised when database operations fail due to connection
    issues, constraint violations, or other database-related problems. It
    serves as a wrapper for database-specific exceptions to maintain
    application-level error handling consistency.

    Attributes:
        message: Description of the database error

    Example:
        try:
            habit_service.save_habit(habit)
        except DatabaseError as e:
            print(f"Database error: {e}")
            # Handle database failure gracefully
    """

    def __init__(self, message: str):
        """Initialize the exception with an error message.

        Args:
            message: Description of the database error
        """
        super().__init__(f"Database error: {message}")
