import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hashlib

from scim_server.main import app
from scim_server.database import Base, get_db
from scim_server.models import ApiKey

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for testing."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Always create a known API key for tests
    key_value = "test-api-key-12345"
    key_hash = hashlib.sha256(key_value.encode()).hexdigest()
    if not session.query(ApiKey).filter(ApiKey.key_hash == key_hash).first():
        api_key = ApiKey(key_hash=key_hash, name="test-key", is_active=True)
        session.add(api_key)
        session.commit()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create test client with database session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_api_key(db_session):
    """Return the known API key for tests."""
    return "test-api-key-12345" 