"""Analytics module with pure functions for read-only data analysis.

This module provides pure functions for analyzing habit tracking data and
calculating streaks. All functions are stateless and do not modify any data,
making them suitable for use in analytics and reporting features.

Key features:
- Longest streak calculations (overall and per habit)
- Streak analysis for daily and weekly habits
- Pure functions that don't modify input data
- Support for both daily and weekly habit periodicity

The functions in this module are designed to be used by the service layer
for providing analytical insights to users about their habit tracking progress.
"""

from datetime import date, timedelta
from typing import List, Optional, Tuple

from models.models import Habit, Completion


def get_longest_streak_overall(
    habits: List[Habit],
    completions_map: dict[int, List[Completion]],
) -> Tuple[List[Habit], int]:
    """Calculate and return all habits with the longest streak.

    Pure function that analyzes completion data to find all habits that share
    the overall longest streak. This function handles ties by returning all
    habits with the maximum streak length. This function is stateless and does
    not modify any input data.

    Args:
        habits: List of Habit objects to analyze
        completions_map: Dictionary mapping habit_id to list of Completion objects

    Returns:
        Tuple of (list of habits with longest streak, streak length).
        Returns ([], 0) if no habits are provided or no completions exist.

    Example:
        >>> habits = [habit1, habit2, habit3]
        >>> completions_map = {1: [comp1, comp2], 2: [comp3, comp4], 3: [comp5]}
        >>> get_longest_streak_overall(habits, completions_map)
        ([habit1, habit2], 2)  # Both habit1 and habit2 have streak of 2
    """
    if not habits:
        return [], 0

    best_streak = 0
    tied_habits = []

    for habit in habits:
        completions = completions_map.get(habit.habit_id, [])
        streak = get_longest_streak_of_a_habit(habit, completions)

        if streak > best_streak:
            best_streak = streak
            tied_habits = [habit]  # Start new list with this habit
        elif streak == best_streak and streak > 0:
            tied_habits.append(habit)  # Add to existing tied list

    return tied_habits, best_streak


def get_longest_streak_of_a_habit(
    habit: Habit,
    completions: List[Completion],
) -> int:
    """Calculate and return the longest streak for a single habit.

    Pure function that computes the longest consecutive completion streak for
    a specific habit. The calculation method depends on the habit's periodicity:
    - Daily habits: counts consecutive days
    - Weekly habits: counts consecutive weeks

    This function is stateless and does not modify any input data.

    Args:
        habit: The Habit object to analyze
        completions: List of Completion objects for this habit, sorted by date

    Returns:
        Length of the longest consecutive streak in the appropriate time unit
        (days for daily habits, weeks for weekly habits)

    Example:
        >>> habit = Habit(habit_id=1, habit_name="Exercise", periodicity="Daily", created_at=datetime.now())
        >>> completions = [Completion(...), Completion(...)]
        >>> get_longest_streak_of_a_habit(habit, completions)
        5
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

    Analyzes a sorted list of completion dates to find the longest sequence
    of consecutive days with completions. A streak is broken when there's a
    gap of more than one day between consecutive dates.

    Args:
        dates: Sorted list of completion dates (ascending order)

    Returns:
        Length of longest consecutive daily streak

    Example:
        >>> dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 5)]
        >>> _longest_daily_streak(dates)
        3  # Days 1-2-3 form the longest streak
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

    Analyzes a sorted list of completion dates to find the longest sequence
    of consecutive weeks with completions. Uses ISO calendar weeks for
    consistent week boundary handling, including proper year boundary
    transitions (e.g., week 52 to week 1).

    Args:
        dates: Sorted list of completion dates (ascending order)

    Returns:
        Length of longest consecutive weekly streak

    Example:
        >>> dates = [date(2025, 1, 6), date(2025, 1, 13), date(2025, 1, 20)]
        >>> _longest_weekly_streak(dates)
        3  # Three consecutive weeks
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
