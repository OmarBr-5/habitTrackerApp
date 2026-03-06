"""Data classes representing core application structures.

This module defines the domain model classes for the Habit Tracker application.
These data classes represent the core entities in the system and are used
throughout the application for data transfer between layers.

The classes are designed to be:
- Immutable data containers
- Independent of business logic
- Serializable for data persistence
- Type-safe with proper annotations

Key entities:
- Habit: Represents a tracked habit with metadata
- Completion: Represents a single completion event for a habit
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Habit:
    """Data class representing a habit without business logic.

    This class represents a single habit that a user wants to track.
    It contains all the metadata about the habit but no business logic
    - that is handled by the service layer.

    Attributes:
        habit_id: Unique identifier for the habit (auto-generated)
        habit_name: Human-readable name for the habit (e.g., "Exercise", "Read Book")
        periodicity: How often the habit should be performed ("Daily" or "Weekly")
        created_at: Timestamp when the habit was created

    Example:
        >>> habit = Habit(
        ...     habit_id=1,
        ...     habit_name="Morning Exercise",
        ...     periodicity="Daily",
        ...     created_at=datetime.now()
        ... )
    """

    habit_id: int
    habit_name: str
    periodicity: str
    created_at: datetime


@dataclass
class Completion:
    """Data class representing a habit completion record.

    This class represents a single instance where a user completed their habit.
    Each completion is linked to a specific habit and records when it was completed.

    Attributes:
        completion_id: Unique identifier for this completion record (auto-generated)
        habit_id: Foreign key linking to the parent Habit
        date_of_completion: When the habit was completed (date and time)

    Example:
        >>> completion = Completion(
        ...     completion_id=1,
        ...     habit_id=1,
        ...     date_of_completion=datetime.now()
        ... )
    """

    completion_id: int
    habit_id: int
    date_of_completion: datetime
