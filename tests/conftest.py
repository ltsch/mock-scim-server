import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Removed hashlib import - no longer needed

from scim_server.main import app
from scim_server.database import Base, get_db, SessionLocal
from scim_server.models import User, Group, Entitlement
from loguru import logger

# Use a separate test database for isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_scim.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def validate_test_environment():
    """Validate that the test environment is properly configured."""
    logger.info("🔍 Validating test environment...")
    
    db = TestingSessionLocal()
    try:
        # API key validation is now handled by config, no database storage needed
        from scim_server.config import settings
        logger.info(f"Using test API key from config: {settings.test_api_key}")
        
        # Check test data
        users = db.query(User).count()
        groups = db.query(Group).count()
        entitlements = db.query(Entitlement).count()
        
        logger.info(f"👥 Found {users} users in test database")
        logger.info(f"🏢 Found {groups} groups in test database")
        logger.info(f"🎫 Found {entitlements} entitlements in test database")
        
        # Validate minimum requirements
        if users < 5:
            raise ValueError(f"Expected at least 5 users in test database, found {users}")
        
        if groups < 5:
            raise ValueError(f"Expected at least 5 groups in test database, found {groups}")
            
        if entitlements < 5:
            raise ValueError(f"Expected at least 5 entitlements in test database, found {entitlements}")
        
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
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Clean up test database after all tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running any tests."""
    # Create test database and populate with minimal test data
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create test session and add minimal test data
        test_session = TestingSessionLocal()
        
        # API key validation is now handled by config, no database storage needed
        from scim_server.config import settings
        logger.info(f"Using test API key from config: {settings.test_api_key}")
        
        # Add minimal test data for validation
        import uuid
        server_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        for test_server_id in server_ids:
            # Only create data if this server doesn't already exist
            if test_session.query(User).filter_by(server_id=test_server_id).count() < 5:
                # Create minimal test users with proper UUIDs
                for i in range(5):
                    user = User(
                        scim_id=str(uuid.uuid4()),
                        user_name=f"testuser{i}@example.com",
                        display_name=f"Test User {i}",
                        email=f"testuser{i}@example.com",
                        active=True,
                        server_id=test_server_id
                    )
                    test_session.add(user)
                # Create minimal test groups with proper UUIDs
                for i in range(5):
                    group = Group(
                        scim_id=str(uuid.uuid4()),
                        display_name=f"Test Group {i}",
                        description=f"Test group {i}",
                        server_id=test_server_id
                    )
                    test_session.add(group)
                # Create minimal test entitlements with proper UUIDs
                for i in range(5):
                    entitlement = Entitlement(
                        scim_id=str(uuid.uuid4()),
                        display_name=f"Test Entitlement {i}",
                        type="License",
                        description=f"Test entitlement {i}",
                        server_id=test_server_id
                    )
                    test_session.add(entitlement)
        test_session.commit()

        # Validate the test environment using the same session
        logger.info("🔍 Validating test environment...")
        for test_server_id in server_ids:
            users = test_session.query(User).filter_by(server_id=test_server_id).count()
            groups = test_session.query(Group).filter_by(server_id=test_server_id).count()
            entitlements = test_session.query(Entitlement).filter_by(server_id=test_server_id).count()
            logger.info(f"Server {test_server_id}: {users} users, {groups} groups, {entitlements} entitlements")
            if users < 5:
                raise ValueError(f"Expected at least 5 users in test database for server {test_server_id}, found {users}")
            if groups < 5:
                raise ValueError(f"Expected at least 5 groups in test database for server {test_server_id}, found {groups}")
            if entitlements < 5:
                raise ValueError(f"Expected at least 5 entitlements in test database for server {test_server_id}, found {entitlements}")
        logger.info("✅ Test environment validation passed for all servers")
        test_session.close()
        
        logger.info("✅ Test environment setup completed")
        
    except Exception as e:
        logger.error(f"❌ Test environment setup failed: {e}")
        raise

@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    session = TestingSessionLocal()
    
    # API key validation is now handled by config, no database storage needed
    from scim_server.config import settings
    logger.info(f"Test session using API key from config: {settings.test_api_key}")
    
    yield session
    
    # Clean up any test-specific data after each test
    try:
        # Rollback any uncommitted changes
        session.rollback()
    except:
        pass
    finally:
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