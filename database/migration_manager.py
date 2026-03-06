"""Database migration and initialization manager.

This module provides database initialization and migration functionality
for the Habit Tracker application. It handles:

- Database schema creation and updates
- Initial data population (predefined habits)
- Database version management
- First-time application setup

The migration manager ensures that the database is properly initialized
and contains the necessary data for the application to function correctly.

Key features:
- Automatic database table creation
- Predefined habit initialization on first run
- Database state detection and management
- Clean separation between schema and data migrations
"""

from pathlib import Path

from database.database import DatabaseConfig
from services.services import HabitService
from repositories.repositories import HabitRepository


class MigrationManager:
    """Manager for database initialization and migrations.

    This class handles the database setup and initialization process for the
    Habit Tracker application. It ensures that the database schema is created
    and populated with initial data when needed.

    Responsibilities:
        - Database schema creation
        - Initial data population (predefined habits)
        - Database state detection
        - First-time application setup

    The migration manager is designed to be idempotent - running it multiple
    times will not cause issues or duplicate data.

    Example:
        >>> migration_manager = MigrationManager()
        >>> migration_manager.initialize_database()
        >>> session = migration_manager.get_session()
    """

    def __init__(self, database_url: str = "sqlite:///habit_tracker.db"):
        """Initialize migration manager.

        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite database
                         in the current directory. Can be customized for different
                         database engines or locations.
        """
        self.db_config = DatabaseConfig(database_url)

    def initialize_database(self) -> None:
        """Initialize the database and create all tables.

        This method performs the complete database initialization process:
        1. Creates all database tables based on ORM models
        2. Checks if the database is empty (first-time launch)
        3. If empty, creates predefined habits to help users get started

        The initialization is designed to be safe to run multiple times:
        - Table creation is idempotent (won't recreate existing tables)
        - Predefined habits are only created if the database is completely empty

        Note:
            This method should be called during application startup to ensure
            the database is properly initialized before any other operations.
        """
        # Create all tables
        self.db_config.create_tables()

        # Check if database is empty and initialize predefined habits if so
        if self._is_database_empty():
            self._create_predefined_habits()

    def _is_database_empty(self) -> bool:
        """Check if the database is empty (no habits exist).

        Performs a simple query to check if any habits exist in the database.
        This is used to determine if this is the first time the application
        is being run and if predefined habits should be created.

        Returns:
            True if no habits exist in the database (empty database)
            False if at least one habit exists (database has data)

        Note:
            This method creates and closes its own database session to avoid
            interfering with any existing transactions or sessions.
        """
        session = self.db_config.get_session()
        try:
            habit_repo = HabitRepository(session)
            habits = habit_repo.fetch_all()
            return len(habits) == 0
        finally:
            session.close()

    def _create_predefined_habits(self) -> None:
        """Create predefined habits in the database.

        Creates a set of sample habits to help users understand how to use
        the application and provide immediate functionality. These habits are
        only created if the database is completely empty (first-time launch).

        Predefined habits include:
        - Wake up early (Daily)
        - Read 10 pages (Daily)
        - Exercise (Daily)
        - Meditation (Daily)
        - Weekly review (Weekly)

        This method uses the HabitService to create the habits, ensuring that
        all business logic and validation rules are properly applied.

        Note:
            This method creates and closes its own database session to ensure
            proper transaction management and avoid conflicts with other operations.
        """
        session = self.db_config.get_session()
        try:
            habit_service = HabitService(session)
            habit_service.init_predefined_habits()
        finally:
            session.close()

    def get_session(self):
        """Get a new database session.

        Returns:
            A new SQLAlchemy session bound to the configured database engine.
            This session can be used for database operations and should be
            closed when finished to return the connection to the pool.

        Example:
            >>> session = migration_manager.get_session()
            >>> try:
            ...     # Perform database operations
            ...     habits = session.query(HabitORM).all()
            ... finally:
            ...     session.close()

        Note:
            This method delegates to the underlying DatabaseConfig instance
            to maintain consistency with how sessions are managed throughout
            the application.
        """
        return self.db_config.get_session()
