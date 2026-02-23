"""Test fixtures and test data for 4-week habit tracking scenarios."""

import datetime
from typing import List, Tuple
from models.models import Habit, Completion


def create_4_week_test_data() -> Tuple[List[Habit], List[Completion]]:
    """Create comprehensive 4-week test data for habit tracking.
    
    Returns:
        Tuple of (habits, completions) for testing
    """
    # Create test habits
    habits = [
        Habit(
            habit_id=1,
            habit_name="Morning Exercise",
            periodicity="Daily",
            created_at=datetime.datetime(2025, 1, 1, 8, 0, 0)
        ),
        Habit(
            habit_id=2,
            habit_name="Read Book",
            periodicity="Daily",
            created_at=datetime.datetime(2025, 1, 1, 19, 0, 0)
        ),
        Habit(
            habit_id=3,
            habit_name="Meditation",
            periodicity="Daily",
            created_at=datetime.datetime(2025, 1, 1, 7, 0, 0)
        ),
        Habit(
            habit_id=4,
            habit_name="Weekly Review",
            periodicity="Weekly",
            created_at=datetime.datetime(2025, 1, 1, 18, 0, 0)
        ),
        Habit(
            habit_id=5,
            habit_name="Gym Session",
            periodicity="Weekly",
            created_at=datetime.datetime(2025, 1, 1, 17, 0, 0)
        ),
    ]
    
    # Base date for 4-week period (starting Monday, January 1, 2025)
    base_date = datetime.date(2025, 1, 1)
    completions = []
    
    # Generate 4 weeks of data
    for week in range(4):
        week_start = base_date + datetime.timedelta(weeks=week)
        
        # Morning Exercise: Daily for first 2 weeks, then skip weekends in week 3, complete all in week 4
        for day in range(7):
            current_date = week_start + datetime.timedelta(days=day)
            if week < 2:  # Complete all days in first 2 weeks
                completions.append(Completion(
                    completion_id=len(completions) + 1,
                    habit_id=1,
                    date_of_completion=datetime.datetime.combine(current_date, datetime.time(8, 0, 0))
                ))
            elif week == 2:  # Skip weekends in week 3
                if day not in [5, 6]:  # Skip Saturday and Sunday
                    completions.append(Completion(
                        completion_id=len(completions) + 1,
                        habit_id=1,
                        date_of_completion=datetime.datetime.combine(current_date, datetime.time(8, 0, 0))
                    ))
            else:  # Complete all days in week 4
                completions.append(Completion(
                    completion_id=len(completions) + 1,
                    habit_id=1,
                    date_of_completion=datetime.datetime.combine(current_date, datetime.time(8, 0, 0))
                ))
        
        # Read Book: Skip every Friday, complete other days
        for day in range(7):
            current_date = week_start + datetime.timedelta(days=day)
            if day != 4:  # Skip Friday (index 4)
                completions.append(Completion(
                    completion_id=len(completions) + 1,
                    habit_id=2,
                    date_of_completion=datetime.datetime.combine(current_date, datetime.time(19, 0, 0))
                ))
        
        # Meditation: Complete Mon-Wed, skip Thu-Fri, complete Sat-Sun
        for day in range(7):
            current_date = week_start + datetime.timedelta(days=day)
            if day in [0, 1, 2, 5, 6]:  # Mon, Tue, Wed, Sat, Sun
                completions.append(Completion(
                    completion_id=len(completions) + 1,
                    habit_id=3,
                    date_of_completion=datetime.datetime.combine(current_date, datetime.time(7, 0, 0))
                ))
        
        # Weekly Review: Complete every Sunday
        sunday_date = week_start + datetime.timedelta(days=6)  # Sunday
        completions.append(Completion(
            completion_id=len(completions) + 1,
            habit_id=4,
            date_of_completion=datetime.datetime.combine(sunday_date, datetime.time(18, 0, 0))
        ))
        
        # Gym Session: Complete every Wednesday
        wednesday_date = week_start + datetime.timedelta(days=2)  # Wednesday
        completions.append(Completion(
            completion_id=len(completions) + 1,
            habit_id=5,
            date_of_completion=datetime.datetime.combine(wednesday_date, datetime.time(17, 0, 0))
        ))
    
    # Add some additional edge cases
    # Habit 1: Add a completion from previous week to test streak continuity
    prev_week_date = base_date - datetime.timedelta(days=1)
    completions.insert(0, Completion(
        completion_id=0,
        habit_id=1,
        date_of_completion=datetime.datetime.combine(prev_week_date, datetime.time(8, 0, 0))
    ))
    
    # Habit 2: Add a completion from next week
    next_week_date = base_date + datetime.timedelta(weeks=4, days=1)
    completions.append(Completion(
        completion_id=len(completions) + 1,
        habit_id=2,
        date_of_completion=datetime.datetime.combine(next_week_date, datetime.time(19, 0, 0))
    ))
    
    return habits, completions


def create_broken_streak_data() -> Tuple[List[Habit], List[Completion]]:
    """Create test data with broken streaks for testing streak calculation edge cases."""
    
    habits = [
        Habit(
            habit_id=1,
            habit_name="Daily Habit with Broken Streak",
            periodicity="Daily",
            created_at=datetime.datetime(2025, 1, 1, 8, 0, 0)
        ),
        Habit(
            habit_id=2,
            habit_name="Weekly Habit with Broken Streak",
            periodicity="Weekly",
            created_at=datetime.datetime(2025, 1, 1, 18, 0, 0)
        ),
    ]
    
    completions = []
    base_date = datetime.date(2025, 1, 1)
    
    # Daily habit: Complete Mon-Tue-Wed, skip Thu-Fri, complete Sat-Sun, then Mon-Tue
    # This creates: 3-day streak, broken, 2-day streak, broken, 2-day streak
    daily_pattern = [0, 1, 2, 5, 6, 7, 8]  # Mon, Tue, Wed, Sat, Sun, next Mon, next Tue
    for day_offset in daily_pattern:
        current_date = base_date + datetime.timedelta(days=day_offset)
        completions.append(Completion(
            completion_id=len(completions) + 1,
            habit_id=1,
            date_of_completion=datetime.datetime.combine(current_date, datetime.time(8, 0, 0))
        ))
    
    # Weekly habit: Complete week 1, skip week 2, complete week 3, skip week 4
    # This creates: 1-week streak, broken, 1-week streak, broken
    weekly_pattern = [0, 2]  # Week 1 and Week 3
    for week_offset in weekly_pattern:
        current_date = base_date + datetime.timedelta(weeks=week_offset)
        completions.append(Completion(
            completion_id=len(completions) + 1,
            habit_id=2,
            date_of_completion=datetime.datetime.combine(current_date, datetime.time(18, 0, 0))
        ))
    
    return habits, completions


def create_empty_data() -> Tuple[List[Habit], List[Completion]]:
    """Create empty test data for edge case testing."""
    return [], []


def create_single_habit_data() -> Tuple[List[Habit], List[Completion]]:
    """Create test data with only one habit for isolated testing."""
    
    habits = [
        Habit(
            habit_id=1,
            habit_name="Single Test Habit",
            periodicity="Daily",
            created_at=datetime.datetime(2025, 1, 1, 8, 0, 0)
        ),
    ]
    
    # Complete every other day for 2 weeks
    completions = []
    base_date = datetime.date(2025, 1, 1)
    for day in range(0, 14, 2):  # Every other day
        current_date = base_date + datetime.timedelta(days=day)
        completions.append(Completion(
            completion_id=len(completions) + 1,
            habit_id=1,
            date_of_completion=datetime.datetime.combine(current_date, datetime.time(8, 0, 0))
        ))
    
    return habits, completions
