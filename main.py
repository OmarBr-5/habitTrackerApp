"""Command-line interface for the Habit Tracker application."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from database.migration_manager import MigrationManager
from services.services import HabitService, CompletionService
from repositories.repositories import HabitRepository
from models.models import Habit
from analytics.analytics_module import (
    get_longest_streak_overall,
    get_longest_streak_of_a_habit,
)
from exceptions.exceptions import (
    HabitTrackerException,
    HabitNotFoundError,
    InvalidPeriodicityError,
)


class HabitTrackerCLI:
    """Command-line interface for Habit Tracker."""

    def __init__(self, database_url: str = "sqlite:///habit_tracker.db"):
        """Initialize CLI with database connection.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.migration_manager = MigrationManager(database_url)
        self.session = None
        self.habit_service = None
        self.completion_service = None
        self.habit_repo = None
        self._first_display = True
    
    def initialize(self) -> None:
        """Initialize the application and database.

        Predefined habits will be created automatically if this is the first-time
        app launch (when the database is empty).
        """
        self.migration_manager.initialize_database()
        self.session = self.migration_manager.get_session()
        self.habit_service = HabitService(self.session)
        self.completion_service = CompletionService(self.session)
        self.habit_repo = HabitRepository(self.session)
    
    def run(self) -> None:
        """Run the main CLI loop."""
        try:
            self.initialize()

            while True:
                self._display_main_menu()
                choice = input("\nEnter your choice: ").strip().lower()
                
                if choice == '1':
                    self._habit_management_menu()
                elif choice == '2':
                    self._show_habits_menu()
                elif choice == '3':
                    self._analytics_dashboard()
                elif choice == '4':
                    self._exit_app()
                    break
                else:
                    print("Invalid choice. Please try again.")
        
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self._cleanup()
    
    def _display_main_menu(self) -> None:
        """Display the main menu."""
        print("\n" + "=" * 50)
        print("📊 HABIT TRACKER APPLICATION")
        print("=" * 50)

        # Show all habits only on first display
        if self._first_display:
            self._show_all_habits_simple()
            self._first_display = False

        print("\n" + "-" * 50)
        print("MENU OPTIONS:")
        print("1. Habit Management")
        print("2. Show Habits (Filtered)")
        print("3. Analytics Dashboard")
        print("4. Exit")
        print("-" * 50)
    
    def _show_all_habits_simple(self) -> None:
        """Display all habits in a simple format."""
        habits = self.habit_repo.fetch_all()
        
        if not habits:
            print("No habits found.")
            return
        
        print("\n📋 YOUR HABITS:")
        for idx, habit in enumerate(habits, 1):
            print(f"{idx}. {habit.habit_name} ({habit.periodicity})")
    
    def _display_habits_with_mapping(self, habits: List[Habit]) -> None:
        """Display habits with UI index to backend ID mapping (internal use only).
        
        5Args:
            habits: List of Habit objects to display
        """
        for idx, habit in enumerate(habits, 1):
            print(f"{idx}. {habit.habit_name} ({habit.periodicity})")
    
    def _get_habit_by_ui_index(self, ui_index: int, habits: List[Habit]) -> Optional[Habit]:
        """Convert UI index to habit object with validation.
        
        Args:
            ui_index: 1-based display index from user input
            habits: List of Habit objects
            
        Returns:
            Habit object if valid index, None otherwise
        """
        if 1 <= ui_index <= len(habits):
            return habits[ui_index - 1]
        return None
    
    def _show_all_habits(self) -> None:
        """Show all habits with detailed information."""
        habits = self.habit_repo.fetch_all()

        if not habits:
            print("\nNo habits found.")
            return

        print("\n" + "=" * 50)
        print("📋 ALL HABITS")
        print("=" * 50)

        for idx, habit in enumerate(habits, 1):
            print(f"\n{idx}. {habit.habit_name}")
            print(f"   ID: {habit.habit_id}")
            print(f"   Periodicity: {habit.periodicity}")
            print(f"   Created: {habit.created_at.strftime('%Y-%m-%d')}")

            # Show streak information
            streak = self.habit_service.calculate_streak(habit.habit_id)
            is_broken = self.habit_service.is_broken(habit.habit_id)
            status = "🔥 ACTIVE" if not is_broken else "❌ BROKEN"
            print(f"   Current Streak: {streak} | Status: {status}")
    
    def _show_habits_menu(self) -> None:
        """Show habits with filtering options."""
        print("\n" + "=" * 50)
        print("🔍 FILTER HABITS")
        print("=" * 50)
        print("1. Show All Habits")
        print("2. Show Daily Habits")
        print("3. Show Weekly Habits")
        print("4. Back to Main Menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == '1':
            self._show_all_habits()
        elif choice == '2':
            self._show_filtered_habits("Daily")
        elif choice == '3':
            self._show_filtered_habits("Weekly")
    
    def _show_filtered_habits(self, periodicity: str) -> None:
        """Show habits filtered by periodicity."""
        habits = self.habit_repo.fetch_by_periodicity(periodicity)
        
        if not habits:
            print(f"\nNo {periodicity} habits found.")
            return
        
        print(f"\n📋 {periodicity.upper()} HABITS:")
        for idx, habit in enumerate(habits, 1):
            streak = self.habit_service.calculate_streak(habit.habit_id)
            print(f"{idx}. {habit.habit_name} - Streak: {streak}")
    
    def _habit_management_menu(self) -> None:
        """Show habit management submenu."""
        print("\n" + "=" * 50)
        print("⚙️  HABIT MANAGEMENT")
        print("=" * 50)
        print("1. Add Habit")
        print("2. Remove Habit")
        print("3. Mark Habit as Completed")
        print("4. Back to Main Menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == '1':
            self._add_habit()
        elif choice == '2':
            self._remove_habit()
        elif choice == '3':
            self._mark_habit_completed()
    
    def _add_habit(self) -> None:
        """Add a new habit."""
        print("\n" + "-" * 50)
        print("➕ ADD NEW HABIT")
        print("-" * 50)
        
        habit_name = input("Enter habit name: ").strip()
        
        print("\nPeriodicity options:")
        print("1. Daily")
        print("2. Weekly")
        periodicity_choice = input("Select periodicity: ").strip()
        
        if periodicity_choice == '1':
            periodicity = "Daily"
        elif periodicity_choice == '2':
            periodicity = "Weekly"
        else:
            print("Invalid choice.")
            return
        
        try:
            habit = self.habit_service.add_habit(habit_name, periodicity)
            print(f"\n✅ Habit '{habit.habit_name}' added successfully!")
        except (InvalidPeriodicityError, Exception) as e:
            print(f"\n❌ Error: {e}")
    
    def _remove_habit(self) -> None:
        """Remove a habit using display index."""
        print("\n" + "-" * 50)
        print("🗑️  REMOVE HABIT")
        print("-" * 50)

        habits = self.habit_repo.fetch_all()
        if not habits:
            print("\nNo habits to remove.")
            return

        print("\n📋 YOUR HABITS:")
        self._display_habits_with_mapping(habits)

        try:
            choice = input("\nEnter the number of the habit to remove: ").strip()

            if choice.isdigit():
                index = int(choice)
                # Map UI index to backend habit object
                habit = self._get_habit_by_ui_index(index, habits)
                
                if habit:
                    # Delete using the backend ID
                    self.habit_service.remove_habit(habit.habit_id)
                    print(f"\n✅ Habit '{habit.habit_name}' (ID: {habit.habit_id}) removed successfully!")
                else:
                    print(f"\n❌ Invalid choice. Please enter a number between 1 and {len(habits)}.")
            else:
                print(f"\n❌ Invalid input. Please enter a number.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def _mark_habit_completed(self) -> None:
        """Mark a habit as completed with clear UI-to-backend mapping."""
        print("\n" + "-" * 50)
        print("✅ MARK HABIT COMPLETE")
        print("-" * 50)

        all_habits = self.habit_repo.fetch_all()
        if not all_habits:
            print("\nNo habits available.")
            return

        print("\n📋 YOUR HABITS:")
        self._display_habits_with_mapping(all_habits)

        user_input = input("\nEnter habit number or name to complete: ").strip()

        try:
            habit = None

            # Try to find by number (display index) - primary method
            if user_input.isdigit():
                index = int(user_input)
                # Map UI index to backend habit object
                habit = self._get_habit_by_ui_index(index, all_habits)
                if not habit and 1 <= index <= len(all_habits):
                    print(f"\n❌ Invalid selection. Please enter a number between 1 and {len(all_habits)}.")
                    return

            # Try to find by name (as fallback)
            if not habit:
                for h in all_habits:
                    if h.habit_name.lower() == user_input.lower():
                        habit = h
                        break

            if habit:
                self.completion_service.mark_habit_as_completed(habit.habit_id)
                print(f"\n✅ '{habit.habit_name}' marked as completed!")
                print(f"   Backend ID: {habit.habit_id}")

                # Show updated streak
                streak = self.habit_service.calculate_streak(habit.habit_id)
                print(f"   Current streak: 🔥 {streak}")
            else:
                print(f"\n❌ Habit '{user_input}' not found.")

        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def _analytics_dashboard(self) -> None:
        """Display analytics dashboard."""
        print("\n" + "=" * 50)
        print("📊 ANALYTICS DASHBOARD")
        print("=" * 50)
        print("1. Show longest streak overall")
        print("2. Show longest streak for a habit")
        print("3. Back to Main Menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == '1':
            self._show_longest_streak_overall()
        elif choice == '2':
            self._show_longest_streak_for_habit()
    
    def _show_longest_streak_overall(self) -> None:
        """Show the habit with the longest streak overall."""
        print("\n" + "=" * 50)
        print("🏆 LONGEST STREAK OVERALL")
        print("=" * 50)

        habits = self.habit_repo.fetch_all()

        if not habits:
            print("\nNo habits to analyze.")
            return

        # Build completions map with integer IDs
        completions_map = {}
        for habit in habits:
            completions_map[habit.habit_id] = self.completion_service.completion_repo.fetch_completions(habit.habit_id)

        # Get longest streak overall
        overall_habit, overall_streak = get_longest_streak_overall(habits, completions_map)
        
        if overall_habit:
            print(f"\n✅ Habit with longest streak: '{overall_habit.habit_name}'")
            print(f"   Streak: {overall_streak} {overall_habit.periodicity}")
            print(f"   Periodicity: {overall_habit.periodicity}")
        else:
            print("\n❌ No streaks found yet. Complete some habits to see streaks!")
    
    def _show_longest_streak_for_habit(self) -> None:
        """Show the longest streak for a specific habit."""
        print("\n" + "=" * 50)
        print("📊 LONGEST STREAK FOR A HABIT")
        print("=" * 50)

        habits = self.habit_repo.fetch_all()

        if not habits:
            print("\nNo habits available.")
            return

        # Display list of habits
        print("\n📋 AVAILABLE HABITS:")
        self._display_habits_with_mapping(habits)

        try:
            user_input = input("\nEnter the number of the habit: ").strip()

            if user_input.isdigit():
                index = int(user_input)
                # Map UI index to backend habit object
                habit = self._get_habit_by_ui_index(index, habits)
                
                if habit:
                    # Get completions for this habit
                    completions = self.completion_service.completion_repo.fetch_completions(habit.habit_id)
                    
                    # Calculate longest streak for this habit
                    longest_streak = get_longest_streak_of_a_habit(habit, completions)
                    
                    print(f"\n✅ Longest streak for '{habit.habit_name}':")
                    print(f"   Streak: {longest_streak} {habit.periodicity}")
                    print(f"   Periodicity: {habit.periodicity}")
                else:
                    print(f"\n❌ Invalid selection. Please enter a number between 1 and {len(habits)}.")
            else:
                print(f"\n❌ Invalid input. Please enter a number.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def _exit_app(self) -> None:
        """Exit the application."""
        print("\n👋 Thank you for using Habit Tracker. Goodbye!")
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            self.session.close()


def main() -> None:
    """Main entry point for the CLI application."""
    cli = HabitTrackerCLI()
    cli.run()


if __name__ == "__main__":
    main()

