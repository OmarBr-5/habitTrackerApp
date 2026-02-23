"""Analytics module with pure functions for read-only data analysis."""

from datetime import date, timedelta
from typing import List, Optional, Tuple

from models.models import Habit, Completion


def get_longest_streak_overall(
    habits: List[Habit],
    completions_map: dict[int, List[Completion]],
) -> Tuple[Optional[Habit], int]:
    """Calculate and return the habit with the longest streak.

    Pure function that analyzes completion data to find the overall longest streak.

    Args:
        habits: List of Habit objects
        completions_map: Dictionary mapping habit_id to list of Completion objects

    Returns:
        Tuple of (Habit with longest streak, streak length). Returns (None, 0) if no habits.
    """
    best_habit: Optional[Habit] = None
    best_streak = 0

    for habit in habits:
        completions = completions_map.get(habit.habit_id, [])
        streak = get_longest_streak_of_a_habit(habit, completions)

        if streak > best_streak:
            best_habit = habit
            best_streak = streak

    return best_habit, best_streak


def get_longest_streak_of_a_habit(
    habit: Habit,
    completions: List[Completion],
) -> int:
    """Calculate and return the longest streak for a single habit.
    
    Pure function that computes the longest consecutive completion streak.
    
    Args:
        habit: The Habit object
        completions: List of Completion objects for this habit
        
    Returns:
        Length of the longest consecutive streak
    """
    if not completions:
        return 0
    
    # Extract and sort completion dates
    completion_dates = sorted([comp.date_of_completion.date() for comp in completions])
    
    if habit.periodicity == "Daily":
        return _longest_daily_streak(completion_dates)
    elif habit.periodicity == "Weekly":
        return _longest_weekly_streak(completion_dates)
    
    return 0


def _longest_daily_streak(dates: List[date]) -> int:
    """Calculate the longest consecutive daily streak.
    
    Args:
        dates: Sorted list of completion dates
        
    Returns:
        Length of longest consecutive daily streak
    """
    if not dates:
        return 0
    
    longest_streak = 1
    current_streak = 1
    
    for i in range(1, len(dates)):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1
    
    return longest_streak


def _longest_weekly_streak(dates: List[date]) -> int:
    """Calculate the longest consecutive weekly streak.
    
    Args:
        dates: Sorted list of completion dates
        
    Returns:
        Length of longest consecutive weekly streak
    """
    if not dates:
        return 0
    
    # Convert to ISO calendar weeks
    weeks = []
    for d in dates:
        iso_year, iso_week, _ = d.isocalendar()
        weeks.append((iso_year, iso_week))
    
    # Remove duplicates within the same week, keep unique weeks
    unique_weeks = []
    for week in weeks:
        if not unique_weeks or unique_weeks[-1] != week:
            unique_weeks.append(week)
    
    if not unique_weeks:
        return 0
    
    longest_streak = 1
    current_streak = 1
    
    for i in range(1, len(unique_weeks)):
        prev_year, prev_week = unique_weeks[i - 1]
        curr_year, curr_week = unique_weeks[i]
        
        # Check if weeks are consecutive
        if prev_year == curr_year and curr_week - prev_week == 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        elif prev_year < curr_year and prev_week == 52 and curr_week == 1:
            # Year boundary case
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1
    
    return longest_streak
