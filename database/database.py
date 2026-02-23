"""Database configuration and ORM models using SQLAlchemy."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class HabitORM(Base):
    """SQLAlchemy ORM model for Habit."""

    __tablename__ = "habits"

    habit_id = Column(Integer, primary_key=True, autoincrement=True)
    habit_name = Column(String, nullable=False, index=True)
    periodicity = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Relationship
    completions = relationship("CompletionORM", back_populates="habit", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<HabitORM(id={self.habit_id}, name={self.habit_name}, periodicity={self.periodicity})>"


class CompletionORM(Base):
    """SQLAlchemy ORM model for Completion."""

    __tablename__ = "completions"

    completion_id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(Integer, ForeignKey("habits.habit_id"), nullable=False, index=True)
    date_of_completion = Column(DateTime, nullable=False, index=True)

    # Relationship
    habit = relationship("HabitORM", back_populates="completions")

    def __repr__(self) -> str:
        return f"<CompletionORM(id={self.completion_id}, habit_id={self.habit_id}, date={self.date_of_completion})>"


class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, database_url: str = "sqlite:///habit_tracker.db"):
        """Initialize database connection.
        
        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite.
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            poolclass=StaticPool if "sqlite" in database_url else None,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
