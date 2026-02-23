"""Database migration and initialization manager."""

from pathlib import Path

from database.database import DatabaseConfig
from services.services import HabitService
from repositories.repositories import HabitRepository


class MigrationManager:
    """Manager for database initialization and migrations."""

    def __init__(self, database_url: str = "sqlite:///habit_tracker.db"):
        """Initialize migration manager.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.db_config = DatabaseConfig(database_url)

    def initialize_database(self) -> None:
        """Initialize the database and create all tables.

        Predefined habits will be created only if the database is empty
        (first-time app launch).
        """
        # Create all tables
        self.db_config.create_tables()

        # Check if database is empty and initialize predefined habits if so
        if self._is_database_empty():
            self._create_predefined_habits()

    def _is_database_empty(self) -> bool:
        """Check if the database is empty (no habits exist).

        Returns:
            True if no habits exist in the database, False otherwise
        """
        session = self.db_config.get_session()
        try:
            habit_repo = HabitRepository(session)
            habits = habit_repo.fetch_all()
            return len(habits) == 0
        finally:
            session.close()

    def _create_predefined_habits(self) -> None:
        """Create predefined habits in the database."""
        session = self.db_config.get_session()
        try:
            habit_service = HabitService(session)
            habit_service.init_predefined_habits()
        finally:
            session.close()

    def get_session(self):
        """Get a new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.db_config.get_session()
