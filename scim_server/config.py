class Settings:
    """Application settings - all configuration in one place."""
    
    # Database settings
    database_url: str = "sqlite:///./scim.db"
    
    # API settings
    max_results_per_page: int = 100
    default_page_size: int = 100
    max_count_limit: int = 1000  # Maximum limit for counting total results
    
    # Security settings
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    rate_limit_create: int = 10  # requests per window for create operations
    rate_limit_read: int = 100   # requests per window for read operations
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 6000
    reload: bool = True
    log_level: str = "debug"
    
    # SCIM settings
    scim_version: str = "2.0"
    
    # API Key settings
    default_api_key: str = "dev-api-key-12345"
    test_api_key: str = "test-api-key-12345"

# Global settings instance
settings = Settings() 