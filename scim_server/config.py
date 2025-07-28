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
    rate_limit_create: int = 500  # requests per window for create operations
    rate_limit_read: int = 500   # requests per window for read operations
    
    # Server settings
    host: str = "0.0.0.0"  # Server binding address
    port: int = 7001
    client_host: str = "localhost"  # Client-facing host for URLs
    reload: bool = True
    log_level: str = "debug"
    
    # Logging settings
    log_to_file: bool = True
    log_file_path: str = "./logs/scim_server.log"
    log_file_rotation: str = "10 MB"  # Rotate when file reaches 10MB
    log_file_retention: str = "7 days"  # Keep logs for 7 days
    log_file_compression: str = "gz"  # Compress rotated logs
    
    # API path settings
    api_base_path: str = ""  # e.g., "/api/v1/scim/dev" - will be combined with "/scim/v2"
    
    # SCIM settings
    scim_version: str = "2.0"
    
    # API Key settings
    default_api_key: str = "api-key-12345"
    test_api_key: str = "test-api-key-12345"
    
    # CLI Tool settings - Default counts for virtual server creation
    cli_default_users: int = 20
    cli_default_groups: int = 10
    cli_default_entitlements: int = 12
    
    # CLI Tool settings - Predefined test data names and types
    cli_group_names: list = [
        "Engineering Team", "Marketing Team", "Sales Team", "HR Team", "Finance Team",
        "Product Team", "Design Team", "Support Team", "Operations Team", "Legal Team"
    ]
    
    # Enhanced Entitlement System - Flexible role/entitlement definitions
    # Each entitlement can have different canonical values and multi-select settings
    
    cli_entitlement_definitions: list = [
        # Application Access - Single select roles
        {
            "name": "Office 365 License",
            "type": "application_access",
            "canonical_values": ["E5", "E3", "Business Basic", "Business Standard", "E1", "F3"],
            "multi_valued": False,
            "description": "Microsoft Office 365 license type"
        },
        {
            "name": "Salesforce Access",
            "type": "application_access", 
            "canonical_values": ["Administrator", "Standard User", "Read Only", "Marketing User", "Contract Manager"],
            "multi_valued": False,
            "description": "Salesforce user access level"
        },
        {
            "name": "GitHub Access",
            "type": "application_access",
            "canonical_values": ["Owner", "Admin", "Write", "Read", "Triage", "Maintain"],
            "multi_valued": False,
            "description": "GitHub repository access level"
        },
        {
            "name": "Slack Access",
            "type": "application_access",
            "canonical_values": ["Owner", "Admin", "Member", "Guest", "Restricted"],
            "multi_valued": False,
            "description": "Slack workspace access level"
        },
        
        # Role-based Access - Multi-select roles
        {
            "name": "System Role",
            "type": "role_based",
            "canonical_values": ["Administrator", "User", "Read-Only", "Auditor", "Manager", "Developer"],
            "multi_valued": True,
            "description": "System-wide role assignments (multi-select)"
        },
        {
            "name": "Security Role",
            "type": "role_based",
            "canonical_values": ["Security Admin", "Security Analyst", "Security Auditor", "Incident Responder", "Threat Hunter"],
            "multi_valued": True,
            "description": "Security-specific role assignments (multi-select)"
        },
        {
            "name": "Data Access Role",
            "type": "role_based",
            "canonical_values": ["Data Owner", "Data Steward", "Data Analyst", "Data Scientist", "Data Engineer"],
            "multi_valued": True,
            "description": "Data access role assignments (multi-select)"
        },
        
        # Permission-based Access - Single select
        {
            "name": "VPN Access",
            "type": "permission_based",
            "canonical_values": ["Full Access", "Limited Access", "Read Only", "No Access"],
            "multi_valued": False,
            "description": "VPN access permission level"
        },
        {
            "name": "Database Access",
            "type": "permission_based",
            "canonical_values": ["Full Access", "Read Write", "Read Only", "No Access"],
            "multi_valued": False,
            "description": "Database access permission level"
        },
        
        # License-based Access - Single select
        {
            "name": "Adobe Creative Suite",
            "type": "license_based",
            "canonical_values": ["Creative Cloud All Apps", "Creative Cloud Single App", "Creative Cloud Photography", "Creative Cloud Design"],
            "multi_valued": False,
            "description": "Adobe Creative Suite license type"
        },
        {
            "name": "AWS Access",
            "type": "license_based",
            "canonical_values": ["AdministratorAccess", "PowerUserAccess", "ReadOnlyAccess", "BillingAccess"],
            "multi_valued": False,
            "description": "AWS IAM access level"
        },
        
        # Department-based Access - Multi-select
        {
            "name": "Department Access",
            "type": "department_based",
            "canonical_values": ["Engineering", "Marketing", "Sales", "HR", "Finance", "Product", "Design", "Support", "Operations", "Legal", "IT", "Research"],
            "multi_valued": True,
            "description": "Department access assignments (multi-select)"
        },
        
        # Project-based Access - Multi-select
        {
            "name": "Project Access",
            "type": "project_based",
            "canonical_values": ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta", "Project Echo"],
            "multi_valued": True,
            "description": "Project access assignments (multi-select)"
        }
    ]
    

    
    # Enhanced CLI Tool settings - Realistic user data generation
    # Using the 'names' module for dynamic name generation
    
    cli_department_job_titles: list = [
        ("Engineering", [
            "Software Engineer", "Senior Software Engineer", "Principal Engineer", "Engineering Manager", 
            "CTO", "DevOps Engineer", "Site Reliability Engineer", "Backend Engineer", "Frontend Engineer",
            "Full Stack Engineer", "Mobile Engineer", "QA Engineer", "Test Engineer"
        ]),
        ("Marketing", [
            "Marketing Manager", "Marketing Specialist", "Marketing Coordinator", "Marketing Director", 
            "Brand Manager", "Digital Marketing Specialist", "Content Marketing Manager", "SEO Specialist",
            "Marketing Analyst", "Product Marketing Manager"
        ]),
        ("Sales", [
            "Sales Representative", "Sales Manager", "Sales Director", "Account Executive", 
            "Business Development Manager", "Sales Engineer", "Inside Sales Representative", "Sales Operations Manager",
            "Regional Sales Manager", "VP of Sales"
        ]),
        ("Human Resources", [
            "HR Manager", "HR Specialist", "HR Coordinator", "Recruiter", "Benefits Administrator",
            "Talent Acquisition Specialist", "HR Business Partner", "Compensation Analyst", "Learning & Development Manager"
        ]),
        ("Finance", [
            "Financial Analyst", "Accountant", "Finance Manager", "Controller", "CFO",
            "Senior Accountant", "Financial Planning Analyst", "Treasury Analyst", "Auditor"
        ]),
        ("Product", [
            "Product Manager", "Product Owner", "Product Director", "Product Analyst", "Product Marketing Manager",
            "Senior Product Manager", "Technical Product Manager", "Product Operations Manager"
        ]),
        ("Design", [
            "UX Designer", "UI Designer", "Graphic Designer", "Design Director", "Creative Director",
            "Senior UX Designer", "Visual Designer", "Interaction Designer", "Design Systems Manager"
        ]),
        ("Support", [
            "Customer Support Specialist", "Support Manager", "Technical Support Engineer", "Customer Success Manager",
            "Support Engineer", "Customer Experience Manager", "Support Team Lead"
        ]),
        ("Operations", [
            "Operations Manager", "Operations Analyst", "Operations Director", "Process Manager",
            "Business Operations Manager", "Operations Coordinator", "Process Improvement Specialist"
        ]),
        ("Legal", [
            "Legal Counsel", "Legal Assistant", "Compliance Officer", "General Counsel",
            "Senior Legal Counsel", "Contract Manager", "Legal Operations Manager"
        ]),
        ("IT", [
            "IT Manager", "System Administrator", "Network Engineer", "IT Support Specialist",
            "IT Director", "Infrastructure Engineer", "IT Security Specialist", "Help Desk Manager"
        ]),
        ("Research", [
            "Research Scientist", "Research Analyst", "Research Director", "Data Analyst",
            "Senior Research Scientist", "Research Manager", "Data Research Analyst"
        ]),
        ("Quality Assurance", [
            "QA Engineer", "Test Engineer", "QA Manager", "Test Lead",
            "Senior QA Engineer", "Automation Engineer", "Test Architect", "QA Analyst"
        ]),
        ("Business Development", [
            "Business Development Representative", "Partnership Manager", "Strategic Partnerships",
            "Business Development Manager", "Partnership Director", "Alliance Manager"
        ]),
        ("Customer Success", [
            "Customer Success Representative", "Customer Success Director", "Account Manager",
            "Customer Success Manager", "Customer Success Specialist", "Customer Experience Director"
        ]),
        ("Data Science", [
            "Data Scientist", "Machine Learning Engineer", "Data Engineer", "Analytics Manager",
            "Senior Data Scientist", "ML Engineer", "Data Architect", "Analytics Director"
        ]),
        ("Security", [
            "Security Engineer", "Security Analyst", "Security Manager", "Information Security Officer",
            "Senior Security Engineer", "Security Architect", "Threat Intelligence Analyst"
        ]),
        ("Compliance", [
            "Compliance Manager", "Compliance Analyst", "Regulatory Affairs Specialist",
            "Senior Compliance Analyst", "Compliance Director", "Risk Manager"
        ]),
        ("Facilities", [
            "Facilities Manager", "Facilities Coordinator", "Office Manager",
            "Facilities Director", "Building Manager", "Facilities Specialist"
        ]),
        ("Procurement", [
            "Procurement Specialist", "Procurement Manager", "Sourcing Manager",
            "Senior Procurement Specialist", "Procurement Director", "Strategic Sourcing Manager"
        ])
    ]
    
    cli_company_domains: list = [
        "example.com", "testcompany.com", "demo-org.com", "scim-test.com", "dev-company.com",
        "mock-enterprise.com", "sample-corp.com", "virtual-org.com", "simulation-inc.com"
    ]
    
    # User attribute distribution settings (percentages)
    cli_user_active_rate: float = 0.90  # 90% of users are active
    cli_user_department_rate: float = 1.0  # 100% of users have departments assigned
    cli_user_job_title_rate: float = 1.0  # 100% of users have job titles
    cli_user_multiple_groups_rate: float = 1.0  # 100% of users belong to multiple groups
    cli_user_entitlements_rate: float = 1.0  # 100% of users have entitlements
    
    # Relationship distribution settings
    cli_max_groups_per_user: int = 6  # Maximum groups a user can belong to
    cli_max_entitlements_per_user: int = 8  # Maximum entitlements a user can have

# Global settings instance
settings = Settings() 