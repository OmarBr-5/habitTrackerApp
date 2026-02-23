"""Data classes representing core application structures."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Habit:
    """Data class representing a habit without business logic.

    Attributes:
        habit_id: Unique identifier for the habit
        habit_name: Human-readable name for the habit
        periodicity: How often the habit occurs ('Daily' or 'Weekly')
        created_at: Timestamp when the habit was created
    """

    habit_id: int
    habit_name: str
    periodicity: str
    created_at: datetime
    


@dataclass
class Completion:
    """Data class representing a habit completion record.

    Attributes:
        completion_id: Unique identifier for this completion record
        habit_id: Foreign key linking to the parent Habit
        date_of_completion: When the habit was completed
    """

    completion_id: int
    habit_id: int
    date_of_completion: datetime
    
