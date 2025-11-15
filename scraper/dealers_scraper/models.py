"""
SQLAlchemy models for BMW dealership scraper.
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Vehicle(Base):
    """Vehicle inventory model."""

    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True)
    dealer = Column(String(255), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    year = Column(Integer, index=True)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False, index=True)
    trim = Column(String(255))
    vin = Column(String(17), unique=True, nullable=False, index=True)
    msrp = Column(Float)
    price = Column(Float, index=True)
    odometer = Column(Integer)
    ext_color = Column(String(100))
    int_color = Column(String(100))
    options = Column(Text)  # JSON array of option codes
    dealer_platform = Column(String(50), nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vehicle(vin='{self.vin}', dealer='{self.dealer}', title='{self.title}')>"


class ScrapeRun(Base):
    """Scrape run tracking model."""

    __tablename__ = 'scrape_runs'

    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='running')  # running, completed, failed
    vehicles_scraped = Column(Integer, default=0)
    dealers_scraped = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    pid = Column(Integer, nullable=True)  # Process ID of subprocess

    def __repr__(self):
        return f"<ScrapeRun(id={self.id}, platform='{self.platform}', status='{self.status}')>"


def get_engine(database_url='sqlite:///data/bmw_inventory.db'):
    """Create and return SQLAlchemy engine."""
    return create_engine(database_url, echo=False)


def get_session(engine):
    """Create and return SQLAlchemy session."""
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(database_url='sqlite:///data/bmw_inventory.db'):
    """Initialize the database by creating all tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


if __name__ == '__main__':
    # Create database when run directly
    print("Initializing database...")
    engine = init_db()
    print("Database initialized successfully at data/bmw_inventory.db")

    # Test creating a session
    session = get_session(engine)
    print(f"Session created: {session}")
    session.close()
    print("Database setup complete!")
