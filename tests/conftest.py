import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hashlib

from scim_server.main import app
from scim_server.database import Base, get_db, SessionLocal
from scim_server.models import ApiKey, User, Group, Entitlement
from loguru import logger

# Use the main database for testing (same as production)
SQLALCHEMY_DATABASE_URL = "sqlite:///./scim.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def validate_test_environment():
    """Validate that the test environment is properly configured."""
    logger.info("🔍 Validating test environment...")
    
    db = SessionLocal()
    try:
        # Check API keys
        api_keys = db.query(ApiKey).count()
        logger.info(f"📋 Found {api_keys} API keys in database")
        
        # Check test data
        users = db.query(User).count()
        groups = db.query(Group).count()
        entitlements = db.query(Entitlement).count()
        
        logger.info(f"👥 Found {users} users in database")
        logger.info(f"🏢 Found {groups} groups in database")
        logger.info(f"🎫 Found {entitlements} entitlements in database")
        
        # Validate minimum requirements
        if users < 5:
            raise ValueError(f"Expected at least 5 users, found {users}. Run 'python scripts/scim_cli.py create'")
        
        if groups < 5:
            raise ValueError(f"Expected at least 5 groups, found {groups}. Run 'python scripts/scim_cli.py create'")
            
        if entitlements < 5:
            raise ValueError(f"Expected at least 5 entitlements, found {entitlements}. Run 'python scripts/scim_cli.py create'")
        

        
        logger.info("✅ Test environment validation passed")
        
    except Exception as e:
        logger.error(f"❌ Test environment validation failed: {e}")
        raise
    finally:
        db.close()

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

@pytest.fixture(scope="session", autouse=True)
def validate_environment():
    """Validate test environment before running any tests."""
    validate_test_environment()

@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    session = SessionLocal()
    
    # Always create a known API key for tests
    from scim_server.config import settings
    key_value = settings.test_api_key
    key_hash = hashlib.sha256(key_value.encode()).hexdigest()
    if not session.query(ApiKey).filter(ApiKey.key_hash == key_hash).first():
        api_key = ApiKey(key_hash=key_hash, name="test-key", is_active=True)
        session.add(api_key)
        session.commit()
    
    yield session
    
    session.close()

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
    from scim_server.config import settings
    return settings.test_api_key 