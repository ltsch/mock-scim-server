from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger
from .config import settings

# Create SQLAlchemy engine using configuration
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False},  # Required for SQLite with multiple threads
    pool_size=20,  # Increase pool size to handle more concurrent connections
    max_overflow=30,  # Increase overflow to handle burst loads
    pool_timeout=60,  # Increase timeout to 60 seconds
    pool_recycle=3600,  # Recycle connections every hour
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully") 