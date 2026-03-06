"""Command-line interface for the Habit Tracker application.

This module provides a comprehensive CLI for managing habits, tracking completions,
and viewing analytics. The application uses a clean architecture with separation
of concerns between presentation, business logic, and data access layers.

Features:
- Add and remove daily/weekly habits
- Mark habits as completed
- View habit lists with filtering options
- Analytics dashboard with streak tracking
- Automatic database initialization with predefined habits
"""

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
    """Command-line interface for Habit Tracker.

    This class provides a user-friendly command-line interface for managing
    habits, tracking completions, and viewing analytics. It handles user input,
    displays menus, and coordinates between the service layer and presentation layer.

    The UI has been enhanced with colored output, table formatting, and more
    descriptive prompts to make the command‑line experience richer and easier
    to read. No third‑party dependencies are required; the enhancements are
    built using ANSI escape sequences which work on most modern terminals.

    Attributes:
        migration_manager: Database migration and initialization manager
        session: SQLAlchemy database session
        habit_service: Service for habit business logic
        completion_service: Service for completion business logic
        habit_repo: Repository for habit data access
        _first_display: Flag to control initial display behavior
    """

    # ANSI escape codes for colors/styles
    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    _GREEN = "\033[92m"
    _YELLOW = "\033[93m"
    _RED = "\033[91m"
    _CYAN = "\033[96m"
    _MAGENTA = "\033[95m"

    def __init__(self, database_url: str = "sqlite:///habit_tracker.db"):
        """Initialize CLI with database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite database
                         in the current directory.
        """
        self.migration_manager = MigrationManager(database_url)
        self.session = None
        self.habit_service = None
        self.completion_service = None
        self.habit_repo = None
        self._first_display = True

    # UI helper methods --------------------------------------------------
    def _color(self, text: str, color: str) -> str:
        """Return colored text using ANSI escape codes."""
        return f"{color}{text}{self._RESET}"

    def _header(self, title: str) -> None:
        """Print a formatted header block with the given title."""
        border = "=" * 50
        print("\n" + self._color(border, self._CYAN))
        print(self._color(self._BOLD + title, self._CYAN))
        print(self._color(border, self._CYAN))

    def _prompt(self, message: str) -> str:
        """Prompt the user with a colored input arrow."""
        return input(self._color(f"⮞ {message}", self._MAGENTA)).strip()

    def _print_success(self, message: str) -> None:
        print(self._color(message, self._GREEN))

    def _print_error(self, message: str) -> None:
        print(self._color(message, self._RED))

    def _print_warning(self, message: str) -> None:
        print(self._color(message, self._YELLOW))

    def initialize(self) -> None:
        """Initialize the application and database.

        This method sets up the database connection, creates necessary tables,
        and initializes predefined habits if the database is empty (first-time launch).

        Predefined habits include:
        - Wake up early (Daily)
        - Read 10 pages (Daily)
        - Exercise (Daily)
        - Meditation (Daily)
        - Weekly review (Weekly)

        Raises:
            Exception: If database initialization fails
        """
        self.migration_manager.initialize_database()
        self.session = self.migration_manager.get_session()
        self.habit_service = HabitService(self.session)
        self.completion_service = CompletionService(self.session)
        self.habit_repo = HabitRepository(self.session)

    def run(self) -> None:
        """Run the main CLI loop.

        This method starts the main application loop, displaying the main menu
        and handling user input until the user chooses to exit. It includes
        proper error handling and resource cleanup.

        The application flow:
        1. Initialize database and services
        2. Display main menu with habit overview
        3. Process user choices (habit management, analytics, etc.)
        4. Continue until user exits
        5. Clean up resources

        Raises:
            Exception: If an unexpected error occurs during execution
        """
        try:
            self.initialize()

            while True:
                self._display_main_menu()
                choice = self._prompt("Enter your choice")
                if not choice:
                    self._print_warning("Please enter a selection.")
                    continue

                if choice == "1":
                    self._habit_management_menu()
                elif choice == "2":
                    self._show_habits_menu()
                elif choice == "3":
                    self._analytics_dashboard()
                elif choice == "4":
                    self._exit_app()
                    break
                else:
                    self._print_error("Invalid choice. Please try again.")
        except Exception as e:
            self._print_error(f"An unexpected error occurred: {e}")
        finally:
            self._cleanup()

    def _display_main_menu(self) -> None:
        """Display the main menu with habit overview.

        Shows the main application menu with options for habit management,
        analytics, and viewing current habits. On first display, also shows
        all existing habits to give the user context.
        """
        self._header("HABIT TRACKER APPLICATION")

        # Show all habits only on first display
        if self._first_display:
            self._show_all_habits_simple()
            self._first_display = False

        # menu options
        print(self._color("\n" + "-" * 50, self._CYAN))
        print(self._color(self._BOLD + "MENU OPTIONS:", self._CYAN))
        print(self._color("1. Habit Management", self._GREEN))
        print(self._color("2. Show Habits (Filtered)", self._GREEN))
        print(self._color("3. Analytics Dashboard", self._GREEN))
        print(self._color("4. Exit", self._GREEN))
        print(self._color("-" * 50, self._CYAN))

    def _show_all_habits_simple(self) -> None:
        """Display all habits in a simple tabular format.

        Shows a basic list of all habits with their names and periodicity.
        This is used for the initial display to give users an overview of
        their current habits. Columns are aligned for easier scanning.
        """
        habits = self.habit_repo.fetch_all()

        if not habits:
            self._print_warning("No habits found.")
            return

        # determine column widths
        name_w = max(len(h.habit_name) for h in habits) if habits else 10
        name_w = max(name_w, 10)
        print(self._color("\nYOUR HABITS:", self._BOLD))
        header = f"{'#':<4}{'Name':<{name_w}}Periodicity"
        print(self._color(header, self._CYAN))
        for idx, habit in enumerate(habits, 1):
            print(f"{idx:<4}{habit.habit_name:<{name_w}}{habit.periodicity}")

    def _display_habits_with_mapping(self, habits: List[Habit]) -> None:
        """Display habits with UI index to backend ID mapping (internal use only).

        Args:
            habits: List of Habit objects to display with numbered indices
        """
        for idx, habit in enumerate(habits, 1):
            print(f"{idx}. {habit.habit_name} ({habit.periodicity})")

    def _get_habit_by_ui_index(
        self, ui_index: int, habits: List[Habit]
    ) -> Optional[Habit]:
        """Convert UI index to habit object with validation.

        Maps a 1-based user interface index to the corresponding Habit object
        from a list. Includes validation to ensure the index is within bounds.

        Args:
            ui_index: 1-based display index from user input (1, 2, 3, etc.)
            habits: List of Habit objects to search

        Returns:
            Habit object if the index is valid, None otherwise

        Example:
            >>> habits = [habit1, habit2, habit3]
            >>> _get_habit_by_ui_index(2, habits)  # Returns habit2
        """
        if 1 <= ui_index <= len(habits):
            return habits[ui_index - 1]
        return None

    def _show_all_habits(self) -> None:
        """Show all habits with detailed information.

        Displays comprehensive information for each habit including:
        - Habit name and ID
        - Periodicity (Daily/Weekly)
        - Creation date
        - Current streak length
        - Streak status (Active/Broken)

        This provides users with a complete overview of their habit tracking progress.
        """
        habits = self.habit_repo.fetch_all()

        if not habits:
            self._print_warning("\nNo habits found.")
            return

        self._header("ALL HABITS")

        # prepare column widths
        name_w = max(len(h.habit_name) for h in habits) if habits else 10
        name_w = max(name_w, 12)
        print(
            self._color(
                f"{'#':<4}{'Name':<{name_w}}Periodicity   Created      Streak   Status",
                self._CYAN,
            )
        )
        for idx, habit in enumerate(habits, 1):
            streak = self.habit_service.calculate_streak(habit.habit_id)
            is_broken = self.habit_service.is_broken(habit.habit_id)
            status = "ACTIVE" if not is_broken else "BROKEN"
            created = habit.created_at.strftime("%Y-%m-%d")
            print(
                f"{idx:<4}{habit.habit_name:<{name_w}}{habit.periodicity:<11}{created:<12}{streak:<8}{status}"
            )

    def _show_habits_menu(self) -> None:
        """Show habits with filtering options.

        Displays a submenu allowing users to view habits filtered by:
        - All habits
        - Daily habits only
        - Weekly habits only

        This helps users focus on specific types of habits they want to review.
        """
        self._header("FILTER HABITS")
        print(self._color("1. Show All Habits", self._GREEN))
        print(self._color("2. Show Daily Habits", self._GREEN))
        print(self._color("3. Show Weekly Habits", self._GREEN))
        print(self._color("4. Back to Main Menu", self._GREEN))

        choice = self._prompt("Enter your choice")

        if choice == "1":
            self._show_all_habits()
        elif choice == "2":
            self._show_filtered_habits("Daily")
        elif choice == "3":
            self._show_filtered_habits("Weekly")

    def _show_filtered_habits(self, periodicity: str) -> None:
        """Show habits filtered by periodicity.

        Displays habits that match the specified periodicity (Daily or Weekly)
        along with their current streak information.

        Args:
            periodicity: String specifying the periodicity to filter by
                        ("Daily" or "Weekly")
        """
        habits = self.habit_repo.fetch_by_periodicity(periodicity)

        if not habits:
            self._print_warning(f"\nNo {periodicity} habits found.")
            return

        print(self._color(f"\n{periodicity.upper()} HABITS:", self._BOLD))
        for idx, habit in enumerate(habits, 1):
            streak = self.habit_service.calculate_streak(habit.habit_id)
            print(f"{idx}. {habit.habit_name} - Streak: {streak}")

    def _habit_management_menu(self) -> None:
        """Show habit management submenu.

        Displays options for managing habits including:
        - Adding new habits
        - Removing existing habits
        - Marking habits as completed

        This is the primary interface for users to interact with their habit data.
        """
        self._header("HABIT MANAGEMENT")
        print(self._color("1. Add Habit", self._GREEN))
        print(self._color("2. Remove Habit", self._GREEN))
        print(self._color("3. Mark Habit as Completed", self._GREEN))
        print(self._color("4. Back to Main Menu", self._GREEN))

        choice = self._prompt("Enter your choice")

        if choice == "1":
            self._add_habit()
        elif choice == "2":
            self._remove_habit()
        elif choice == "3":
            self._mark_habit_completed()

    def _add_habit(self) -> None:
        """Add a new habit.

        Prompts the user for a habit name and periodicity, then creates
        the new habit in the database. Validates input and provides
        appropriate error messages for invalid entries.

        User Input:
            - Habit name (text)
            - Periodicity (1 for Daily, 2 for Weekly)

        Raises:
            InvalidPeriodicityError: If periodicity is not Daily or Weekly
            Exception: If habit creation fails
        """
        self._header("ADD NEW HABIT")

        habit_name = self._prompt("Enter habit name")

        print(self._color("\nPeriodicity options:", self._CYAN))
        print(self._color("1. Daily", self._GREEN))
        print(self._color("2. Weekly", self._GREEN))
        periodicity_choice = self._prompt("Select periodicity")

        if periodicity_choice == "1":
            periodicity = "Daily"
        elif periodicity_choice == "2":
            periodicity = "Weekly"
        else:
            self._print_error("Invalid choice.")
            return

        try:
            habit = self.habit_service.add_habit(habit_name, periodicity)
            self._print_success(f"\nHabit '{habit.habit_name}' added successfully!")
        except (InvalidPeriodicityError, Exception) as e:
            self._print_error(f"\nError: {e}")

    def _remove_habit(self) -> None:
        """Remove a habit using display index.

        Displays the current list of habits with numbered indices, then
        prompts the user to select which habit to remove by number.
        Validates the selection and removes the habit from the database.

        User Input:
            - Habit number from the displayed list

        Raises:
            Exception: If habit removal fails
        """
        self._header("REMOVE HABIT")

        habits = self.habit_repo.fetch_all()
        if not habits:
            self._print_warning("\nNo habits to remove.")
            return

        print(self._color("\n📋 YOUR HABITS:", self._BOLD))
        self._display_habits_with_mapping(habits)

        try:
            choice = self._prompt("Enter the number of the habit to remove")

            if choice.isdigit():
                index = int(choice)
                # Map UI index to backend habit object
                habit = self._get_habit_by_ui_index(index, habits)

                if habit:
                    # Delete using the backend ID
                    self.habit_service.remove_habit(habit.habit_id)
                    self._print_success(
                        f"\nHabit '{habit.habit_name}' (ID: {habit.habit_id}) removed successfully!"
                    )
                else:
                    self._print_error(
                        f"\nInvalid choice. Please enter a number between 1 and {len(habits)}."
                    )
            else:
                self._print_error(f"\nInvalid input. Please enter a number.")
        except Exception as e:
            self._print_error(f"\nError: {e}")

    def _mark_habit_completed(self) -> None:
        """Mark a habit as completed with clear UI-to-backend mapping.

        Allows users to mark a habit as completed either by:
        - Selecting from a numbered list of habits
        - Typing the habit name directly

        Validates the selection, records the completion with the current date/time,
        and displays updated streak information.

        User Input:
            - Habit number or habit name

        Raises:
            Exception: If completion recording fails
        """
        self._header("MARK HABIT COMPLETE")

        all_habits = self.habit_repo.fetch_all()
        if not all_habits:
            self._print_warning("\nNo habits available.")
            return

        print(self._color("\n📋 YOUR HABITS:", self._BOLD))
        self._display_habits_with_mapping(all_habits)

        user_input = self._prompt("Enter habit number or name to complete")

        try:
            habit = None

            # Try to find by number (display index) - primary method
            if user_input.isdigit():
                index = int(user_input)
                # Map UI index to backend habit object
                habit = self._get_habit_by_ui_index(index, all_habits)
                if not habit and 1 <= index <= len(all_habits):
                    self._print_error(
                        f"\n❌ Invalid selection. Please enter a number between 1 and {len(all_habits)}."
                    )
                    return

            # Try to find by name (as fallback)
            if not habit:
                for h in all_habits:
                    if h.habit_name.lower() == user_input.lower():
                        habit = h
                        break

            if habit:
                self.completion_service.mark_habit_as_completed(habit.habit_id)
                self._print_success(f"\n'{habit.habit_name}' marked as completed!")
                print(self._color(f"   Backend ID: {habit.habit_id}", self._CYAN))

                # Show updated streak
                streak = self.habit_service.calculate_streak(habit.habit_id)
                print(self._color(f"   Current streak: {streak}", self._BOLD))
            else:
                self._print_error(f"\nHabit '{user_input}' not found.")

        except Exception as e:
            self._print_error(f"\nError: {e}")

    def _analytics_dashboard(self) -> None:
        """Display analytics dashboard.

        Shows a submenu with various analytical views of habit data including:
        - Longest streak overall across all habits
        - Longest streak for a specific habit

        This helps users understand their habit tracking patterns and progress.
        """
        self._header("ANALYTICS DASHBOARD")
        print(self._color("1. Show longest streak overall", self._GREEN))
        print(self._color("2. Show longest streak for a habit", self._GREEN))
        print(self._color("3. Back to Main Menu", self._GREEN))

        choice = self._prompt("Enter your choice")

        if choice == "1":
            self._show_longest_streak_overall()
        elif choice == "2":
            self._show_longest_streak_for_habit()

    def _show_longest_streak_overall(self) -> None:
        """Show all habits with the longest streak overall.

        Calculates and displays all habits that share the longest consecutive streak
        across all tracked habits. Handles ties by showing all habits with the
        maximum streak length. This provides motivation and insight into
        the user's most consistent habits.
        """
        self._header("LONGEST STREAK OVERALL")

        habits = self.habit_repo.fetch_all()

        if not habits:
            print("\nNo habits to analyze.")
            return

        # Build completions map with integer IDs
        completions_map = {}
        for habit in habits:
            completions_map[habit.habit_id] = (
                self.completion_service.completion_repo.fetch_completions(
                    habit.habit_id
                )
            )

        # Get all habits with longest streak
        tied_habits, overall_streak = get_longest_streak_overall(
            habits, completions_map
        )

        if not tied_habits:
            print("\n❌ No streaks found yet. Complete some habits to see streaks!")
            return

        # Display results
        if len(tied_habits) == 1:
            habit = tied_habits[0]
            self._print_success(f"\nHabit with longest streak: '{habit.habit_name}'")
            print(
                self._color(
                    f"   Streak: {overall_streak} {habit.periodicity}", self._BOLD
                )
            )
            print(self._color(f"   Periodicity: {habit.periodicity}", self._CYAN))
        else:
            self._print_warning(
                f"\nTIED FOR LONGEST STREAK ({overall_streak} {tied_habits[0].periodicity}):"
            )
            for i, habit in enumerate(tied_habits, 1):
                print(
                    self._color(
                        f"   {i}. {habit.habit_name} ({habit.periodicity})",
                        self._MAGENTA,
                    )
                )

            self._print_warning(
                f"\nYou have {len(tied_habits)} habits tied for the longest streak!"
            )

    def _show_longest_streak_for_habit(self) -> None:
        """Show the longest streak for a specific habit.

        Allows users to select a specific habit and view its longest
        consecutive streak. This helps users understand their performance
        patterns for individual habits.

        User Input:
            - Habit number from the displayed list
        """
        self._header("LONGEST STREAK FOR A HABIT")

        habits = self.habit_repo.fetch_all()

        if not habits:
            print("\nNo habits available.")
            return

        # Display list of habits
        print(self._color("\nAVAILABLE HABITS:", self._BOLD))
        self._display_habits_with_mapping(habits)

        try:
            user_input = input("\nEnter the number of the habit: ").strip()

            if user_input.isdigit():
                index = int(user_input)
                # Map UI index to backend habit object
                habit = self._get_habit_by_ui_index(index, habits)

                if habit:
                    # Get completions for this habit
                    completions = (
                        self.completion_service.completion_repo.fetch_completions(
                            habit.habit_id
                        )
                    )

                    # Calculate longest streak for this habit
                    longest_streak = get_longest_streak_of_a_habit(habit, completions)

                    print(f"\nLongest streak for '{habit.habit_name}':")
                    print(f"   Streak: {longest_streak} {habit.periodicity}")
                    print(f"   Periodicity: {habit.periodicity}")
                else:
                    print(
                        f"\nInvalid selection. Please enter a number between 1 and {len(habits)}."
                    )
            else:
                print(f"\nInvalid input. Please enter a number.")
        except Exception as e:
            print(f"\nError: {e}")

    def _exit_app(self) -> None:
        """Exit the application.

        Displays a farewell message and gracefully terminates the application.
        """
        print("\nThank you for using Habit Tracker. Goodbye!")

    def _cleanup(self) -> None:
        """Clean up resources.

        Properly closes the database session to prevent resource leaks.
        This method is called automatically when the application exits.
        """
        if self.session:
            self.session.close()


def main() -> None:
    """Main entry point for the CLI application.

    Creates and runs the HabitTrackerCLI instance. This function serves as the
    starting point when the module is executed directly.

    Usage:
        python main.py
    """
    cli = HabitTrackerCLI()
    cli.run()


if __name__ == "__main__":
    main()
