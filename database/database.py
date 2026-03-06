"""Database configuration and ORM models using SQLAlchemy.

This module provides the database layer implementation for the Habit Tracker
application using SQLAlchemy ORM. It includes:

- ORM model definitions for Habit and Completion entities
- Database configuration and connection management
- Session factory for database operations
- Table creation and schema management

The database layer follows the repository pattern and provides a clean
abstraction between the application logic and the underlying database.

Database schema:
- habits table: Stores habit metadata
- completions table: Stores completion records with foreign key to habits
- Uses SQLite by default for simplicity and portability
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class HabitORM(Base):
    """SQLAlchemy ORM model for Habit.

    This class represents the database schema for habits. It maps directly
    to the 'habits' table in the database and provides an object-oriented
    interface for database operations.

    Database fields:
        habit_id: Auto-incrementing primary key
        habit_name: Text field with index for fast lookups
        periodicity: Text field storing 'Daily' or 'Weekly'
        created_at: Timestamp when the record was created

    Relationships:
        completions: One-to-many relationship with CompletionORM records
                   Uses cascade delete to automatically remove completions
                   when a habit is deleted

    Example:
        >>> habit = HabitORM(habit_name="Exercise", periodicity="Daily")
        >>> session.add(habit)
        >>> session.commit()
    """

    __tablename__ = "habits"

    habit_id = Column(Integer, primary_key=True, autoincrement=True)
    habit_name = Column(String, nullable=False, index=True)
    periodicity = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Relationship
    completions = relationship(
        "CompletionORM", back_populates="habit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<HabitORM(id={self.habit_id}, name={self.habit_name}, periodicity={self.periodicity})>"


class CompletionORM(Base):
    """SQLAlchemy ORM model for Completion.

    This class represents the database schema for habit completions. It maps
    directly to the 'completions' table and provides an object-oriented interface
    for tracking when habits were completed.

    Database fields:
        completion_id: Auto-incrementing primary key
        habit_id: Foreign key referencing the parent habit
        date_of_completion: Timestamp when the habit was completed

    Relationships:
        habit: Many-to-one relationship with HabitORM
             Each completion belongs to exactly one habit

    Indexes:
        - habit_id: For fast lookups of completions by habit
        - date_of_completion: For fast date-based queries and sorting

    Example:
        >>> completion = CompletionORM(
        ...     habit_id=1,
        ...     date_of_completion=datetime.now()
        ... )
        >>> session.add(completion)
        >>> session.commit()
    """

    __tablename__ = "completions"

    completion_id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(
        Integer, ForeignKey("habits.habit_id"), nullable=False, index=True
    )
    date_of_completion = Column(DateTime, nullable=False, index=True)

    # Relationship
    habit = relationship("HabitORM", back_populates="completions")

    def __repr__(self) -> str:
        return f"<CompletionORM(id={self.completion_id}, habit_id={self.habit_id}, date={self.date_of_completion})>"


class DatabaseConfig:
    """Database configuration and session management.

    This class handles database connection configuration, session management,
    and table creation. It provides a centralized way to manage database
    operations and ensures consistent database access throughout the application.

    Features:
        - Configurable database URL (supports SQLite, PostgreSQL, MySQL, etc.)
        - Session factory for creating database sessions
        - Table creation and schema management
        - Connection pooling configuration

    Example:
        >>> db_config = DatabaseConfig("sqlite:///app.db")
        >>> db_config.create_tables()
        >>> session = db_config.get_session()
        >>> # Use session for database operations
        >>> session.close()
    """

    def __init__(self, database_url: str = "sqlite:///habit_tracker.db"):
        """Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite database
                         in the current directory. Supports various database
                         engines including SQLite, PostgreSQL, MySQL, etc.

        Note:
            For SQLite databases, special connection arguments are used to
            support in-memory databases and thread safety.
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            connect_args=(
                {"check_same_thread": False} if "sqlite" in database_url else {}
            ),
            poolclass=StaticPool if "sqlite" in database_url else None,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables.

        Creates the database schema by creating all tables defined in the
        ORM models. This method should be called during application
        initialization to ensure the database structure is in place.

        Note:
            This method uses SQLAlchemy's create_all() which is idempotent -
            it will only create tables that don't already exist.
        """
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get a new database session.

        Returns:
            A new SQLAlchemy session bound to the configured engine.
            The session should be closed when finished to return the
            connection to the pool.

        Example:
            >>> session = db_config.get_session()
            >>> try:
            ...     # Perform database operations
            ...     session.commit()
            ... except Exception:
            ...     session.rollback()
            ... finally:
            ...     session.close()
        """
        return self.SessionLocal()
