class Settings:
    """Application settings - all configuration in one place."""
    
    # Database settings
    database_url: str = "sqlite:///./scim.db"
    
    # API settings
    max_results_per_page: int = 100
    default_page_size: int = 100
    max_count_limit: int = 1000  # Maximum limit for counting total results
    
    # Security settings
    rate_limit_requests: int = 500
    rate_limit_window: int = 30  # seconds
    rate_limit_create: int = 60  # requests per window for create operations
    rate_limit_read: int = 500   # requests per window for read operations
    
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
    
    # CLI Tool settings - Default counts for virtual server creation
    cli_default_users: int = 10
    cli_default_groups: int = 5
    cli_default_entitlements: int = 8
    cli_default_roles: int = 4
    
    # CLI Tool settings - Predefined test data names and types
    cli_group_names: list = [
        "Engineering Team", "Marketing Team", "Sales Team", "HR Team", "Finance Team",
        "Product Team", "Design Team", "Support Team", "Operations Team", "Legal Team"
    ]
    
    cli_entitlement_types: list = [
        ("Office 365 License", "License"),
        ("Salesforce Access", "Profile"),
        ("GitHub Access", "Profile"),
        ("Slack Access", "Profile"),
        ("Jira Access", "Profile"),
        ("Confluence Access", "Profile"),
        ("AWS Access", "Profile"),
        ("GCP Access", "Profile"),
        ("Azure Access", "Profile"),
        ("VPN Access", "Profile")
    ]
    
    cli_role_names: list = [
        "Developer", "Manager", "Admin", "Analyst", "Designer"
    ]

# Global settings instance
settings = Settings() 