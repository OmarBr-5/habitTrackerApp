"""Habit tracker package - SRP-based architecture."""

__version__ = "2.0.0"

from exceptions.exceptions import (
    HabitTrackerException,
    HabitNotFoundError,
    InvalidHabitError,
    InvalidPeriodicityError,
)

__all__ = [
    "HabitTrackerException",
    "HabitNotFoundError",
    "InvalidHabitError",
    "InvalidPeriodicityError",
]

