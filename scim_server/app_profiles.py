"""
App Profiles Configuration

This module defines different app profiles that surface specific sets of user data,
user roles, user entitlements, and have unique mutability requirements for different
application contexts.

This system integrates with the existing config.py settings rather than replacing them.

PROFILE MUTABILITY RULES:
- READ_ONLY: Attribute can be read but never modified after creation
- READ_WRITE: Attribute can be read and modified at any time
- IMMUTABLE: Attribute cannot be changed once set (even during creation)
- WRITE_ONCE: Attribute can be set during creation but never modified after

ACCEPTABLE VALUES:
- Email addresses: Must be valid email format, can include multiple addresses with types (work, home, other)
- Phone numbers: Must be valid phone format, can include multiple numbers with types (work, mobile, home, other)
- Addresses: Complex objects with streetAddress, locality, region, postalCode, country
- Employee numbers: String format, typically alphanumeric
- Job titles: Free text, should match organizational standards
- Departments: Must match compatible_departments list for the profile
- Entitlements: Must match compatible_entitlements list for the profile

PROFILE-SPECIFIC RULES:
- HR Profile: Full employee lifecycle management, includes sensitive HR data
- IT Profile: System administration focus, includes technical access controls
- Sales Profile: Customer-facing data, includes territory and commission information
- Marketing Profile: Campaign and content management, includes creative tool access
- Finance Profile: Financial data access, includes budget and accounting information
- Legal Profile: Compliance and legal document access, includes audit trails
- Operations Profile: Business process management, includes workflow and analytics
- Security Profile: Security operations focus, includes access control and monitoring
- Customer Success Profile: Customer relationship management, includes support tools
- Research Profile: Data analysis focus, includes research tools and databases
- Engineering Profile: Software development focus, includes development tools and repositories
- Product Profile: Product management focus, includes product tools and roadmaps
- Support Profile: Technical support focus, includes support tools and knowledge bases
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from loguru import logger
from .config import settings

class AppType(Enum):
    """Supported application types."""
    HR = "hr"
    IT = "it"
    SALES = "sales"
    MARKETING = "marketing"
    FINANCE = "finance"
    LEGAL = "legal"
    OPERATIONS = "operations"
    SECURITY = "security"
    CUSTOMER_SUCCESS = "customer_success"
    RESEARCH = "research"
    # New common profiles
    ENGINEERING = "engineering"
    PRODUCT = "product"
    SUPPORT = "support"

class MutabilityLevel(Enum):
    """Mutability levels for different attributes."""
    READ_ONLY = "readOnly"
    READ_WRITE = "readWrite"
    IMMUTABLE = "immutable"
    WRITE_ONCE = "writeOnce"

@dataclass
class AttributeConfig:
    """Configuration for a specific attribute."""
    name: str
    mutability: MutabilityLevel
    required: bool = False
    visible: bool = True
    description: Optional[str] = None

@dataclass
class RoleConfig:
    """Configuration for roles in an app profile."""
    name: str
    description: str
    permissions: List[str]
    mutability: MutabilityLevel = MutabilityLevel.READ_WRITE

@dataclass
class EntitlementConfig:
    """Configuration for entitlements in an app profile."""
    name: str
    type: str
    canonical_values: List[str]
    multi_valued: bool = False
    mutability: MutabilityLevel = MutabilityLevel.READ_WRITE
    description: Optional[str] = None

@dataclass
class AppProfileConfig:
    """Complete configuration for an app profile."""
    app_type: AppType
    name: str
    description: str
    user_attributes: List[AttributeConfig]
    roles: List[RoleConfig]
    entitlements: List[EntitlementConfig]
    data_filters: Dict[str, Any]
    mutability_rules: Dict[str, MutabilityLevel]
    # Integration with existing config
    compatible_entitlements: List[str]  # Names from cli_entitlement_definitions
    compatible_departments: List[str]   # Departments from cli_department_job_titles
    compatible_groups: List[str]        # Groups from cli_group_names
    version: str = "1.0"  # Profile version for tracking changes

class AppProfileManager:
    """
    Manages app profile configurations and operations.
    
    This class provides a centralized way to manage different application profiles
    that define how user data is accessed, modified, and filtered based on the
    application context (HR, IT, Sales, etc.).
    
    USAGE EXAMPLES:
    
    # Get a specific profile
    manager = AppProfileManager()
    hr_profile = manager.get_profile(AppType.HR)
    
    # Check if an attribute can be modified
    can_modify = manager.validate_attribute_mutability(
        AppType.HR, "employeeNumber", "write"
    )
    
    # Get visible attributes for a profile
    visible_attrs = manager.get_visible_attributes(AppType.IT)
    
    # Get compatible entitlements for a profile
    entitlements = manager.get_compatible_entitlements(AppType.SALES)
    
    PROFILE INTEGRATION:
    - Each profile defines what user attributes are visible and modifiable
    - Profiles specify which entitlements, departments, and groups are compatible
    - Profiles include data filters that determine what user data is accessible
    - Profiles define mutability rules that control what can be changed and when
    
    COMPLIANCE CONSIDERATIONS:
    - HR profiles have strict data protection requirements
    - IT profiles require security and access control compliance
    - Finance profiles must comply with financial regulations
    - Legal profiles must maintain attorney-client privilege
    - All profiles must respect data privacy and consent requirements
    """
    
    def __init__(self):
        self.profiles = self._initialize_profiles()
    
    def _initialize_profiles(self) -> Dict[AppType, AppProfileConfig]:
        """Initialize all app profile configurations."""
        return {
            AppType.HR: self._create_hr_profile(),
            AppType.IT: self._create_it_profile(),
            AppType.SALES: self._create_sales_profile(),
            AppType.MARKETING: self._create_marketing_profile(),
            AppType.FINANCE: self._create_finance_profile(),
            AppType.LEGAL: self._create_legal_profile(),
            AppType.OPERATIONS: self._create_operations_profile(),
            AppType.SECURITY: self._create_security_profile(),
            AppType.CUSTOMER_SUCCESS: self._create_customer_success_profile(),
            AppType.RESEARCH: self._create_research_profile(),
            AppType.ENGINEERING: self._create_engineering_profile(),
            AppType.PRODUCT: self._create_product_profile(),
            AppType.SUPPORT: self._create_support_profile(),
        }
    
    def _create_hr_profile(self) -> AppProfileConfig:
        """
        Create HR app profile configuration.
        
        HR Profile Context:
        - Purpose: Full employee lifecycle management from hire to termination
        - Data Sensitivity: HIGH - Contains sensitive personal and employment information
        - Access Control: Strict role-based access with audit trails
        - Compliance: Must comply with employment law and data protection regulations
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE and cannot be changed after assignment
        - Hire dates are WRITE_ONCE and represent the official employment start date
        - Usernames are READ_ONLY to prevent identity confusion
        - SCIM IDs are IMMUTABLE for system integrity
        
        Acceptable Values:
        - Employee numbers: Alphanumeric strings, typically 6-10 characters
        - Hire dates: ISO 8601 format (YYYY-MM-DD)
        - Job titles: Standard organizational titles (e.g., "Software Engineer", "HR Manager")
        - Departments: Must be from compatible_departments list
        - Cost centers: Alphanumeric codes representing budget allocation
        - Job codes: Standardized job classification codes
        
        Data Filters:
        - Includes inactive employees for historical records
        - Includes contractors for complete workforce view
        - Includes managers for organizational hierarchy
        """
        return AppProfileConfig(
            app_type=AppType.HR,
            name="Human Resources",
            description="HR application profile for employee management and HR operations",
            version="1.1",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                AttributeConfig("postalCode", MutabilityLevel.READ_WRITE, required=False, description="Postal code"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("hireDate", MutabilityLevel.WRITE_ONCE, required=True, description="Employment start date"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                AttributeConfig("costCenter", MutabilityLevel.READ_WRITE, required=False, description="Cost center"),
                AttributeConfig("jobCode", MutabilityLevel.READ_WRITE, required=False, description="Job classification"),
                
                # Additional HR-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("HR Manager", "Full HR management access", ["read", "write", "delete", "approve"]),
                RoleConfig("HR Specialist", "HR operations access", ["read", "write"]),
                RoleConfig("HR Coordinator", "Basic HR access", ["read", "write"]),
                RoleConfig("Recruiter", "Recruitment access", ["read", "write"]),
                RoleConfig("Benefits Admin", "Benefits management access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("HR System Access", "application_access", ["Full Access", "Read Only", "No Access"]),
                EntitlementConfig("Payroll Access", "application_access", ["Full Access", "Read Only", "No Access"]),
                EntitlementConfig("Benefits Access", "application_access", ["Full Access", "Read Only", "No Access"]),
                EntitlementConfig("Recruitment Access", "application_access", ["Full Access", "Read Only", "No Access"]),
                EntitlementConfig("Performance Access", "application_access", ["Full Access", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Human Resources", "Recruiting", "Benefits", "Compensation"],
                "include_inactive": True,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
                "hireDate": MutabilityLevel.WRITE_ONCE,
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
            },
            compatible_entitlements=["System Role", "Department Access"],
            compatible_departments=["Human Resources"],
            compatible_groups=["HR Team"],
        )
    
    def _create_it_profile(self) -> AppProfileConfig:
        """
        Create IT app profile configuration.
        
        IT Profile Context:
        - Purpose: System administration, technical access control, and IT operations
        - Data Sensitivity: HIGH - Contains system access and security information
        - Access Control: Technical role-based access with elevated privileges
        - Compliance: Must comply with IT security policies and access management standards
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for system account consistency
        - Usernames are READ_ONLY to prevent system access issues
        - SCIM IDs are IMMUTABLE for system integration integrity
        - Technical entitlements require approval workflows
        
        Acceptable Values:
        - Job titles: Technical titles (e.g., "System Administrator", "DevOps Engineer")
        - Departments: IT, Engineering, DevOps, Infrastructure, Security
        - Entitlements: Technical access (GitHub, AWS, VPN, Database, etc.)
        - Locations: Office locations or remote work designations
        - Cost centers: IT budget allocation codes
        
        Data Filters:
        - Excludes inactive employees for security
        - Includes contractors for complete IT workforce
        - Includes managers for technical leadership roles
        - Focuses on technical departments and roles
        """
        return AppProfileConfig(
            app_type=AppType.IT,
            name="Information Technology",
            description="IT application profile for system administration and IT operations",
            version="1.1",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                AttributeConfig("costCenter", MutabilityLevel.READ_WRITE, required=False, description="Cost center"),
                AttributeConfig("jobCode", MutabilityLevel.READ_WRITE, required=False, description="Job classification"),
                
                # IT-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("IT Administrator", "Full IT system access", ["read", "write", "delete", "admin"]),
                RoleConfig("System Administrator", "System administration access", ["read", "write", "admin"]),
                RoleConfig("Network Administrator", "Network administration access", ["read", "write", "admin"]),
                RoleConfig("Help Desk", "Help desk access", ["read", "write"]),
                RoleConfig("IT Support", "IT support access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("IT System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Network Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Security Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Infrastructure Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Support Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["IT", "Engineering", "DevOps", "Infrastructure", "Security"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "GitHub Access", "Slack Access", "VPN Access", "Database Access", "AWS Access", "System Role", "Security Role", "Department Access"],
            compatible_departments=["IT", "Engineering"],
            compatible_groups=["Engineering Team", "Support Team", "Operations Team"],
        )
    
    def _create_sales_profile(self) -> AppProfileConfig:
        """
        Create Sales app profile configuration.
        
        Sales Profile Context:
        - Purpose: Sales operations, customer relationship management, and revenue tracking
        - Data Sensitivity: MEDIUM - Contains customer and sales performance information
        - Access Control: Sales role-based access with territory management
        - Compliance: Must comply with sales policies and customer data protection
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for sales tracking consistency
        - Usernames are READ_ONLY to prevent CRM integration issues
        - SCIM IDs are IMMUTABLE for sales system integration
        - Territory assignments may be restricted by management approval
        
        Acceptable Values:
        - Job titles: Sales titles (e.g., "Sales Representative", "Account Executive")
        - Departments: Sales, Business Development, Account Management
        - Entitlements: Sales tools (Salesforce, CRM, Commission systems)
        - Territories: Geographic or account-based territory assignments
        - Commission structures: Sales performance tracking codes
        
        Data Filters:
        - Excludes inactive employees for active sales focus
        - Includes contractors for complete sales workforce
        - Includes managers for sales leadership and oversight
        - Focuses on revenue-generating roles and departments
        """
        return AppProfileConfig(
            app_type=AppType.SALES,
            name="Sales",
            description="Sales application profile for sales operations and customer management",
            version="1.1",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                # Sales-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Sales Manager", "Sales management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Sales Representative", "Sales operations access", ["read", "write"]),
                RoleConfig("Account Executive", "Account management access", ["read", "write"]),
                RoleConfig("Sales Engineer", "Sales engineering access", ["read", "write"]),
                RoleConfig("Business Development", "Business development access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Sales System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("CRM Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Sales Tools Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Commission Access", "application_access", ["Full Access", "Read Only", "No Access"]),
                EntitlementConfig("Territory Access", "application_access", ["Full Access", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Sales", "Business Development", "Account Management"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Salesforce Access", "Office 365 License", "Slack Access", "System Role", "Department Access", "Project Access"],
            compatible_departments=["Sales", "Business Development"],
            compatible_groups=["Sales Team"],
        )
    
    def _create_marketing_profile(self) -> AppProfileConfig:
        """
        Create Marketing app profile configuration.
        
        Marketing Profile Context:
        - Purpose: Marketing operations, campaign management, and brand communications
        - Data Sensitivity: MEDIUM - Contains campaign data and creative content access
        - Access Control: Marketing role-based access with creative tool permissions
        - Compliance: Must comply with marketing policies and brand guidelines
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for campaign attribution consistency
        - Usernames are READ_ONLY to prevent creative tool access issues
        - SCIM IDs are IMMUTABLE for marketing system integration
        - Creative tool access requires brand compliance approval
        
        Acceptable Values:
        - Job titles: Marketing titles (e.g., "Marketing Specialist", "Brand Manager")
        - Departments: Marketing, Digital Marketing, Content Marketing, Brand
        - Entitlements: Creative tools (Adobe Creative Suite, Marketing platforms)
        - Campaign access: Marketing campaign and analytics platform permissions
        - Content permissions: Brand asset and content management access
        
        Data Filters:
        - Excludes inactive employees for active campaign focus
        - Includes contractors for complete marketing workforce
        - Includes managers for marketing leadership and brand oversight
        - Focuses on creative and marketing communication roles
        """
        return AppProfileConfig(
            app_type=AppType.MARKETING,
            name="Marketing",
            description="Marketing application profile for marketing operations and campaign management",
            version="1.1",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                # Marketing-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Marketing Manager", "Marketing management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Marketing Specialist", "Marketing operations access", ["read", "write"]),
                RoleConfig("Digital Marketing", "Digital marketing access", ["read", "write"]),
                RoleConfig("Content Marketing", "Content marketing access", ["read", "write"]),
                RoleConfig("Brand Manager", "Brand management access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Marketing System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Campaign Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Analytics Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Social Media Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Content Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Marketing", "Digital Marketing", "Content Marketing", "Brand"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Adobe Creative Suite", "Office 365 License", "Slack Access", "System Role", "Department Access", "Project Access"],
            compatible_departments=["Marketing"],
            compatible_groups=["Marketing Team"],
        )
    
    def _create_finance_profile(self) -> AppProfileConfig:
        """
        Create Finance app profile configuration.
        
        Finance Profile Context:
        - Purpose: Financial operations, accounting, budgeting, and financial reporting
        - Data Sensitivity: HIGH - Contains financial data, budgets, and accounting information
        - Access Control: Finance role-based access with strict financial controls
        - Compliance: Must comply with financial regulations, SOX, and audit requirements
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for financial tracking consistency
        - Usernames are READ_ONLY to prevent financial system access issues
        - SCIM IDs are IMMUTABLE for financial system integration integrity
        - Cost centers are READ_WRITE but require approval for changes
        - Financial data access requires additional audit logging
        
        Acceptable Values:
        - Job titles: Finance titles (e.g., "Accountant", "Financial Analyst", "Controller")
        - Departments: Finance, Accounting, Treasury, Audit
        - Entitlements: Financial systems (ERP, Accounting software, Budget tools)
        - Cost centers: Valid budget allocation codes with approval workflow
        - Job codes: Standardized financial role classifications
        
        Data Filters:
        - Includes inactive employees for financial historical records
        - Includes contractors for complete financial workforce view
        - Includes managers for financial oversight and approval roles
        - Focuses on financial and accounting departments
        """
        return AppProfileConfig(
            app_type=AppType.FINANCE,
            name="Finance",
            description="Finance application profile for financial operations and accounting",
            version="1.1",
            user_attributes=[
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                AttributeConfig("costCenter", MutabilityLevel.READ_WRITE, required=False, description="Cost center"),
                AttributeConfig("jobCode", MutabilityLevel.READ_WRITE, required=False, description="Job classification"),
                
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Finance Manager", "Finance management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Accountant", "Accounting access", ["read", "write"]),
                RoleConfig("Financial Analyst", "Financial analysis access", ["read", "write"]),
                RoleConfig("Controller", "Controller access", ["read", "write", "approve"]),
                RoleConfig("CFO", "CFO access", ["read", "write", "delete", "approve", "admin"]),
            ],
            entitlements=[
                EntitlementConfig("Finance System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Accounting Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Budget Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Reporting Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Audit Access", "application_access", ["Full Access", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Finance", "Accounting", "Treasury", "Audit"],
                "include_inactive": True,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
                "costCenter": MutabilityLevel.READ_WRITE,
            },
            compatible_entitlements=["Office 365 License", "Database Access", "System Role", "Department Access", "Data Access Role"],
            compatible_departments=["Finance"],
            compatible_groups=["Finance Team"],
        )
    
    def _create_legal_profile(self) -> AppProfileConfig:
        """
        Create Legal app profile configuration.
        
        Legal Profile Context:
        - Purpose: Legal operations, compliance management, contract administration, and regulatory affairs
        - Data Sensitivity: HIGH - Contains legal documents, compliance data, and privileged information
        - Access Control: Legal role-based access with attorney-client privilege considerations
        - Compliance: Must comply with legal ethics, data retention, and privilege protection
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for legal record consistency
        - Usernames are READ_ONLY to prevent legal system access issues
        - SCIM IDs are IMMUTABLE for legal system integration integrity
        - Legal document access requires privilege level verification
        - Compliance data changes require legal review and approval
        
        Acceptable Values:
        - Job titles: Legal titles (e.g., "Legal Counsel", "Compliance Officer", "General Counsel")
        - Departments: Legal, Compliance, Regulatory Affairs
        - Entitlements: Legal systems (Document management, Contract systems, Compliance tools)
        - Privilege levels: Attorney, Paralegal, Legal Assistant, Compliance Officer
        - Document access: Legal document and contract management permissions
        
        Data Filters:
        - Includes inactive employees for legal historical records
        - Includes contractors for complete legal workforce view
        - Includes managers for legal oversight and compliance roles
        - Focuses on legal and compliance departments
        """
        return AppProfileConfig(
            app_type=AppType.LEGAL,
            name="Legal",
            description="Legal application profile for legal operations and compliance",
            version="1.1",
            user_attributes=[
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                AttributeConfig("costCenter", MutabilityLevel.READ_WRITE, required=False, description="Cost center"),
                AttributeConfig("jobCode", MutabilityLevel.READ_WRITE, required=False, description="Job classification"),
                
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Legal Counsel", "Legal counsel access", ["read", "write", "approve"]),
                RoleConfig("Legal Assistant", "Legal assistant access", ["read", "write"]),
                RoleConfig("Compliance Officer", "Compliance access", ["read", "write", "approve"]),
                RoleConfig("General Counsel", "General counsel access", ["read", "write", "delete", "approve", "admin"]),
                RoleConfig("Contract Manager", "Contract management access", ["read", "write", "approve"]),
            ],
            entitlements=[
                EntitlementConfig("Legal System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Compliance Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Contract Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Document Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Audit Access", "application_access", ["Full Access", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Legal", "Compliance", "Regulatory Affairs"],
                "include_inactive": True,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "Database Access", "System Role", "Department Access", "Security Role"],
            compatible_departments=["Legal"],
            compatible_groups=["Legal Team"],
        )
    
    def _create_operations_profile(self) -> AppProfileConfig:
        """
        Create Operations app profile configuration.
        
        Operations Profile Context:
        - Purpose: Business operations, process management, workflow administration, and operational analytics
        - Data Sensitivity: MEDIUM - Contains operational data, process information, and business metrics
        - Access Control: Operations role-based access with process management permissions
        - Compliance: Must comply with operational policies and business process standards
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for operational tracking consistency
        - Usernames are READ_ONLY to prevent operational system access issues
        - SCIM IDs are IMMUTABLE for operational system integration integrity
        - Process changes require operational review and approval
        
        Acceptable Values:
        - Job titles: Operations titles (e.g., "Operations Manager", "Business Analyst", "Process Manager")
        - Departments: Operations, Business Operations, Process Improvement
        - Entitlements: Operations systems (Workflow tools, Analytics platforms, Process management)
        - Process access: Business process and workflow management permissions
        - Analytics access: Operational reporting and analytics platform access
        
        Data Filters:
        - Excludes inactive employees for active operations focus
        - Includes contractors for complete operational workforce
        - Includes managers for operational oversight and process leadership
        - Focuses on business operations and process management roles
        """
        return AppProfileConfig(
            app_type=AppType.OPERATIONS,
            name="Operations",
            description="Operations application profile for business operations and process management",
            version="1.1",
            user_attributes=[
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Operations Manager", "Operations management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Operations Analyst", "Operations analysis access", ["read", "write"]),
                RoleConfig("Process Manager", "Process management access", ["read", "write", "approve"]),
                RoleConfig("Business Analyst", "Business analysis access", ["read", "write"]),
                RoleConfig("Operations Coordinator", "Operations coordination access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Operations System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Process Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Analytics Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Reporting Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Workflow Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Operations", "Business Operations", "Process Improvement"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "Database Access", "System Role", "Department Access", "Data Access Role", "Project Access"],
            compatible_departments=["Operations"],
            compatible_groups=["Operations Team"],
        )
    
    def _create_security_profile(self) -> AppProfileConfig:
        """
        Create Security app profile configuration.
        
        Security Profile Context:
        - Purpose: Security operations, access control, threat management, and security monitoring
        - Data Sensitivity: HIGH - Contains security data, access controls, and threat intelligence
        - Access Control: Security role-based access with elevated security privileges
        - Compliance: Must comply with security policies, SOC 2, and cybersecurity standards
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for security tracking consistency
        - Usernames are READ_ONLY to prevent security system access issues
        - SCIM IDs are IMMUTABLE for security system integration integrity
        - Security access requires additional background checks and approval
        - Security data changes require security team review and approval
        
        Acceptable Values:
        - Job titles: Security titles (e.g., "Security Engineer", "Security Analyst", "Security Manager")
        - Departments: Security, Information Security, Cybersecurity
        - Entitlements: Security systems (Access control, Threat intelligence, Security monitoring)
        - Security clearances: Required security clearance levels and access permissions
        - Incident response: Security incident response and monitoring tool access
        
        Data Filters:
        - Includes inactive employees for security historical records
        - Includes contractors for complete security workforce view
        - Includes managers for security oversight and incident response leadership
        - Focuses on security and cybersecurity departments
        """
        return AppProfileConfig(
            app_type=AppType.SECURITY,
            name="Security",
            description="Security application profile for security operations and access control",
            version="1.1",
            user_attributes=[
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Security Manager", "Security management access", ["read", "write", "delete", "approve", "admin"]),
                RoleConfig("Security Engineer", "Security engineering access", ["read", "write", "approve"]),
                RoleConfig("Security Analyst", "Security analysis access", ["read", "write"]),
                RoleConfig("Security Auditor", "Security audit access", ["read", "write", "approve"]),
                RoleConfig("Incident Responder", "Incident response access", ["read", "write", "approve"]),
            ],
            entitlements=[
                EntitlementConfig("Security System Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Access Control", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Threat Intelligence", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Vulnerability Management", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Security Monitoring", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Security", "Information Security", "Cybersecurity"],
                "include_inactive": True,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["VPN Access", "Database Access", "AWS Access", "System Role", "Security Role", "Department Access"],
            compatible_departments=["Security"],
            compatible_groups=["Operations Team"],  # Security often part of operations
        )
    
    def _create_customer_success_profile(self) -> AppProfileConfig:
        """
        Create Customer Success app profile configuration.
        
        Customer Success Profile Context:
        - Purpose: Customer relationship management, customer support, and customer experience optimization
        - Data Sensitivity: MEDIUM - Contains customer data, support interactions, and customer feedback
        - Access Control: Customer success role-based access with customer data permissions
        - Compliance: Must comply with customer data protection and support policies
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for customer interaction tracking consistency
        - Usernames are READ_ONLY to prevent customer support system access issues
        - SCIM IDs are IMMUTABLE for customer success system integration integrity
        - Customer data access requires customer consent and privacy compliance
        
        Acceptable Values:
        - Job titles: Customer success titles (e.g., "Customer Success Manager", "Support Specialist")
        - Departments: Customer Success, Customer Support, Account Management
        - Entitlements: Customer success platforms (CRM, Support systems, Customer portals)
        - Customer access: Customer relationship and support tool permissions
        - Feedback systems: Customer feedback and experience management access
        
        Data Filters:
        - Excludes inactive employees for active customer focus
        - Includes contractors for complete customer success workforce
        - Includes managers for customer success leadership and oversight
        - Focuses on customer-facing roles and departments
        """
        return AppProfileConfig(
            app_type=AppType.CUSTOMER_SUCCESS,
            name="Customer Success",
            description="Customer Success application profile for customer management and support",
            version="1.1",
            user_attributes=[
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Customer Success Manager", "Customer success management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Customer Success Representative", "Customer success operations access", ["read", "write"]),
                RoleConfig("Account Manager", "Account management access", ["read", "write"]),
                RoleConfig("Support Specialist", "Support operations access", ["read", "write"]),
                RoleConfig("Customer Experience", "Customer experience access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Customer Success Platform", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Support System", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Customer Portal", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Analytics Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Feedback System", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Customer Success", "Customer Support", "Account Management"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "Slack Access", "System Role", "Department Access", "Project Access"],
            compatible_departments=["Customer Success"],
            compatible_groups=["Support Team"],
        )
    
    def _create_research_profile(self) -> AppProfileConfig:
        """
        Create Research app profile configuration.
        
        Research Profile Context:
        - Purpose: Research operations, data analysis, statistical modeling, and research collaboration
        - Data Sensitivity: MEDIUM - Contains research data, analytical models, and research findings
        - Access Control: Research role-based access with data analysis permissions
        - Compliance: Must comply with research ethics, data privacy, and intellectual property protection
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for research attribution consistency
        - Usernames are READ_ONLY to prevent research system access issues
        - SCIM IDs are IMMUTABLE for research system integration integrity
        - Research data access requires research ethics approval and data protection compliance
        
        Acceptable Values:
        - Job titles: Research titles (e.g., "Research Scientist", "Data Scientist", "Research Analyst")
        - Departments: Research, Data Science, Analytics
        - Entitlements: Research platforms (Statistical software, Research databases, Analytics tools)
        - Data access: Research data and analytical tool permissions
        - Publication systems: Research publication and collaboration platform access
        
        Data Filters:
        - Excludes inactive employees for active research focus
        - Includes contractors for complete research workforce
        - Includes managers for research oversight and collaboration leadership
        - Focuses on research and data analysis roles
        """
        return AppProfileConfig(
            app_type=AppType.RESEARCH,
            name="Research",
            description="Research application profile for research operations and data analysis",
            version="1.1",
            user_attributes=[
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Research Manager", "Research management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Research Scientist", "Research operations access", ["read", "write"]),
                RoleConfig("Data Scientist", "Data science access", ["read", "write"]),
                RoleConfig("Research Analyst", "Research analysis access", ["read", "write"]),
                RoleConfig("Research Director", "Research direction access", ["read", "write", "approve"]),
            ],
            entitlements=[
                EntitlementConfig("Research Platform", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Data Analysis Tools", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Statistical Software", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Research Database", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Publication System", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Research", "Data Science", "Analytics"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "Database Access", "AWS Access", "System Role", "Department Access", "Data Access Role", "Project Access"],
            compatible_departments=["Research", "Data Science"],
            compatible_groups=["Product Team"],  # Research often part of product
        )
    
    def _create_engineering_profile(self) -> AppProfileConfig:
        """
        Create Engineering app profile configuration.
        
        Engineering Profile Context:
        - Purpose: Software development, engineering operations, code management, and technical collaboration
        - Data Sensitivity: MEDIUM - Contains source code, development data, and technical infrastructure access
        - Access Control: Engineering role-based access with development tool permissions
        - Compliance: Must comply with software development policies, code security, and intellectual property protection
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for development tracking consistency
        - Usernames are READ_ONLY to prevent development system access issues
        - SCIM IDs are IMMUTABLE for development system integration integrity
        - Code repository access requires code review and security approval
        
        Acceptable Values:
        - Job titles: Engineering titles (e.g., "Software Engineer", "DevOps Engineer", "QA Engineer")
        - Departments: Engineering, Software Development, DevOps, QA
        - Entitlements: Development tools (GitHub, CI/CD, Cloud infrastructure, Monitoring tools)
        - Code access: Source code repository and development environment permissions
        - Infrastructure access: Cloud and infrastructure management tool access
        
        Data Filters:
        - Excludes inactive employees for active development focus
        - Includes contractors for complete engineering workforce
        - Includes managers for engineering leadership and technical oversight
        - Focuses on software development and engineering roles
        """
        return AppProfileConfig(
            app_type=AppType.ENGINEERING,
            name="Engineering",
            description="Engineering application profile for software development and engineering operations",
            version="1.0",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                # Engineering-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred programming language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Engineering Manager", "Engineering management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Senior Engineer", "Senior engineering access", ["read", "write", "approve"]),
                RoleConfig("Software Engineer", "Software engineering access", ["read", "write"]),
                RoleConfig("DevOps Engineer", "DevOps engineering access", ["read", "write"]),
                RoleConfig("QA Engineer", "Quality assurance access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Development Environment", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Code Repository", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("CI/CD Pipeline", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Cloud Infrastructure", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Monitoring Tools", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Engineering", "Software Development", "DevOps", "QA"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["GitHub Access", "Slack Access", "AWS Access", "Database Access", "System Role", "Department Access"],
            compatible_departments=["Engineering"],
            compatible_groups=["Engineering Team"],
        )
    
    def _create_product_profile(self) -> AppProfileConfig:
        """
        Create Product app profile configuration.
        
        Product Profile Context:
        - Purpose: Product management, product development, user experience design, and product strategy
        - Data Sensitivity: MEDIUM - Contains product data, user research, and product roadmap information
        - Access Control: Product role-based access with product tool permissions
        - Compliance: Must comply with product development policies, user data protection, and intellectual property protection
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for product tracking consistency
        - Usernames are READ_ONLY to prevent product system access issues
        - SCIM IDs are IMMUTABLE for product system integration integrity
        - Product roadmap access requires product strategy approval
        
        Acceptable Values:
        - Job titles: Product titles (e.g., "Product Manager", "Product Owner", "UX Designer")
        - Departments: Product, Product Management, UX, Design
        - Entitlements: Product tools (Product management platforms, Analytics tools, Design tools)
        - Product access: Product management and roadmap tool permissions
        - User research: User research and analytics platform access
        
        Data Filters:
        - Excludes inactive employees for active product focus
        - Includes contractors for complete product workforce
        - Includes managers for product leadership and strategy oversight
        - Focuses on product management and user experience roles
        """
        return AppProfileConfig(
            app_type=AppType.PRODUCT,
            name="Product",
            description="Product application profile for product management and development",
            version="1.0",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                # Product-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Product Manager", "Product management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Product Owner", "Product ownership access", ["read", "write", "approve"]),
                RoleConfig("Product Analyst", "Product analysis access", ["read", "write"]),
                RoleConfig("UX Designer", "User experience design access", ["read", "write"]),
                RoleConfig("Product Marketing", "Product marketing access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Product Management Platform", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Analytics Tools", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Design Tools", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("User Research", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Roadmap Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Product", "Product Management", "UX", "Design"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "Slack Access", "System Role", "Department Access", "Project Access"],
            compatible_departments=["Product"],
            compatible_groups=["Product Team"],
        )
    
    def _create_support_profile(self) -> AppProfileConfig:
        """
        Create Support app profile configuration.
        
        Support Profile Context:
        - Purpose: Technical support, customer assistance, knowledge management, and support operations
        - Data Sensitivity: MEDIUM - Contains support interactions, customer data, and technical troubleshooting information
        - Access Control: Support role-based access with support tool permissions
        - Compliance: Must comply with support policies, customer data protection, and technical documentation standards
        
        Key Restrictions:
        - Employee numbers are WRITE_ONCE for support tracking consistency
        - Usernames are READ_ONLY to prevent support system access issues
        - SCIM IDs are IMMUTABLE for support system integration integrity
        - Customer data access requires customer consent and privacy compliance
        
        Acceptable Values:
        - Job titles: Support titles (e.g., "Support Specialist", "Technical Support", "Customer Support")
        - Departments: Support, Customer Support, Technical Support
        - Entitlements: Support tools (Support platforms, Knowledge bases, Remote access tools)
        - Support access: Support system and knowledge base permissions
        - Escalation systems: Support escalation and case management tool access
        
        Data Filters:
        - Excludes inactive employees for active support focus
        - Includes contractors for complete support workforce
        - Includes managers for support leadership and oversight
        - Focuses on customer support and technical assistance roles
        """
        return AppProfileConfig(
            app_type=AppType.SUPPORT,
            name="Support",
            description="Support application profile for customer support and technical assistance",
            version="1.0",
            user_attributes=[
                # Core SCIM attributes
                AttributeConfig("userName", MutabilityLevel.READ_ONLY, required=True, description="Unique username"),
                AttributeConfig("displayName", MutabilityLevel.READ_WRITE, required=True, description="Full display name"),
                AttributeConfig("givenName", MutabilityLevel.READ_WRITE, required=True, description="First name"),
                AttributeConfig("familyName", MutabilityLevel.READ_WRITE, required=True, description="Last name"),
                AttributeConfig("active", MutabilityLevel.READ_WRITE, required=True, description="Account status"),
                
                # Email addresses (multiple)
                AttributeConfig("emails", MutabilityLevel.READ_WRITE, required=True, description="Email addresses (work, personal)"),
                
                # Phone numbers (multiple)
                AttributeConfig("phoneNumbers", MutabilityLevel.READ_WRITE, required=False, description="Phone numbers (work, mobile)"),
                
                # Location information
                AttributeConfig("addresses", MutabilityLevel.READ_WRITE, required=False, description="Address information"),
                AttributeConfig("city", MutabilityLevel.READ_WRITE, required=False, description="City"),
                AttributeConfig("state", MutabilityLevel.READ_WRITE, required=False, description="State/Province"),
                AttributeConfig("country", MutabilityLevel.READ_WRITE, required=False, description="Country"),
                
                # Employment details
                AttributeConfig("title", MutabilityLevel.READ_WRITE, required=True, description="Job title"),
                AttributeConfig("department", MutabilityLevel.READ_WRITE, required=True, description="Department"),
                AttributeConfig("employeeNumber", MutabilityLevel.WRITE_ONCE, required=True, description="Employee ID"),
                AttributeConfig("manager", MutabilityLevel.READ_WRITE, required=False, description="Manager reference"),
                AttributeConfig("location", MutabilityLevel.READ_WRITE, required=False, description="Office location"),
                
                # Support-specific attributes
                AttributeConfig("preferredLanguage", MutabilityLevel.READ_WRITE, required=False, description="Preferred language"),
                AttributeConfig("timezone", MutabilityLevel.READ_WRITE, required=False, description="Time zone"),
                AttributeConfig("locale", MutabilityLevel.READ_WRITE, required=False, description="Locale preference"),
            ],
            roles=[
                RoleConfig("Support Manager", "Support management access", ["read", "write", "delete", "approve"]),
                RoleConfig("Senior Support", "Senior support access", ["read", "write", "approve"]),
                RoleConfig("Support Specialist", "Support operations access", ["read", "write"]),
                RoleConfig("Technical Support", "Technical support access", ["read", "write"]),
                RoleConfig("Customer Support", "Customer support access", ["read", "write"]),
            ],
            entitlements=[
                EntitlementConfig("Support Platform", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Knowledge Base", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Customer Database", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Remote Access", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
                EntitlementConfig("Escalation System", "application_access", ["Full Access", "Read Write", "Read Only", "No Access"]),
            ],
            data_filters={
                "departments": ["Support", "Customer Support", "Technical Support"],
                "include_inactive": False,
                "include_contractors": True,
                "include_managers": True,
            },
            mutability_rules={
                "userName": MutabilityLevel.READ_ONLY,
                "scim_id": MutabilityLevel.IMMUTABLE,
                "employeeNumber": MutabilityLevel.WRITE_ONCE,
            },
            compatible_entitlements=["Office 365 License", "Slack Access", "System Role", "Department Access"],
            compatible_departments=["Support"],
            compatible_groups=["Support Team"],
        )

    def get_profile(self, app_type: AppType) -> Optional[AppProfileConfig]:
        """Get a specific app profile configuration."""
        return self.profiles.get(app_type)
    
    def get_all_profiles(self) -> Dict[AppType, AppProfileConfig]:
        """Get all app profile configurations."""
        return self.profiles
    
    def get_profile_by_name(self, name: str) -> Optional[AppProfileConfig]:
        """Get a profile by its name."""
        for profile in self.profiles.values():
            if profile.name.lower() == name.lower():
                return profile
        return None
    
    def validate_attribute_mutability(self, app_type: AppType, attribute_name: str, operation: str) -> bool:
        """
        Validate if an attribute can be modified for a given app type and operation.
        
        This method checks whether a specific attribute can be read, written, created,
        or deleted based on the profile's mutability rules and the requested operation.
        
        Args:
            app_type: The application profile type (HR, IT, Sales, etc.)
            attribute_name: The name of the attribute to validate
            operation: The operation to validate ("read", "write", "create", "delete")
            
        Returns:
            bool: True if the operation is allowed, False otherwise
            
        Examples:
            # Check if employee number can be written in HR profile
            can_write = manager.validate_attribute_mutability(
                AppType.HR, "employeeNumber", "write"
            )  # Returns False (WRITE_ONCE)
            
            # Check if username can be read in IT profile
            can_read = manager.validate_attribute_mutability(
                AppType.IT, "userName", "read"
            )  # Returns True (READ_ONLY)
            
        Mutability Rules:
        - READ_ONLY: Can only be read, never modified
        - READ_WRITE: Can be read and modified at any time
        - IMMUTABLE: Cannot be changed once set (even during creation)
        - WRITE_ONCE: Can be set during creation but never modified after
        """
        profile = self.get_profile(app_type)
        if not profile:
            return False
        
        # Find the attribute configuration
        attr_config = None
        for attr in profile.user_attributes:
            if attr.name == attribute_name:
                attr_config = attr
                break
        
        if not attr_config:
            return False
        
        # Check mutability rules
        if operation == "read":
            return attr_config.visible
        elif operation == "write":
            return attr_config.mutability in [MutabilityLevel.READ_WRITE, MutabilityLevel.WRITE_ONCE]
        elif operation == "create":
            return attr_config.mutability in [MutabilityLevel.READ_WRITE, MutabilityLevel.WRITE_ONCE]
        elif operation == "delete":
            return attr_config.mutability == MutabilityLevel.READ_WRITE
        
        return False
    
    def get_visible_attributes(self, app_type: AppType) -> List[str]:
        """
        Get list of visible attributes for a given app type.
        
        This method returns all user attributes that are visible (accessible)
        for a specific application profile. Visible attributes can be read
        and potentially modified based on their mutability rules.
        
        Args:
            app_type: The application profile type (HR, IT, Sales, etc.)
            
        Returns:
            List[str]: List of attribute names that are visible for this profile
            
        Examples:
            # Get all visible attributes for HR profile
            hr_attrs = manager.get_visible_attributes(AppType.HR)
            # Returns: ['userName', 'displayName', 'givenName', 'familyName', 'active', 'emails', ...]
            
            # Get all visible attributes for IT profile
            it_attrs = manager.get_visible_attributes(AppType.IT)
            # Returns: ['userName', 'displayName', 'givenName', 'familyName', 'active', 'emails', ...]
            
        Note:
            - All attributes in the profile are visible by default
            - The 'visible' flag can be used to hide specific attributes if needed
            - Visible attributes can still have different mutability levels
        """
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return [attr.name for attr in profile.user_attributes if attr.visible]
    
    def get_required_attributes(self, app_type: AppType) -> List[str]:
        """Get list of required attributes for a given app type."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return [attr.name for attr in profile.user_attributes if attr.required]
    
    def get_roles(self, app_type: AppType) -> List[RoleConfig]:
        """Get roles for a given app type."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return profile.roles
    
    def get_entitlements(self, app_type: AppType) -> List[EntitlementConfig]:
        """Get entitlements for a given app type."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return profile.entitlements
    
    def get_compatible_entitlements(self, app_type: AppType) -> List[str]:
        """
        Get compatible entitlement names from existing config for a given app type.
        
        This method returns the list of entitlement names that are compatible
        with a specific application profile. These entitlements can be assigned
        to users within that profile context.
        
        Args:
            app_type: The application profile type (HR, IT, Sales, etc.)
            
        Returns:
            List[str]: List of compatible entitlement names for this profile
            
        Examples:
            # Get compatible entitlements for HR profile
            hr_entitlements = manager.get_compatible_entitlements(AppType.HR)
            # Returns: ['System Role', 'Department Access']
            
            # Get compatible entitlements for IT profile
            it_entitlements = manager.get_compatible_entitlements(AppType.IT)
            # Returns: ['Office 365 License', 'GitHub Access', 'Slack Access', 'VPN Access', ...]
            
            # Get compatible entitlements for Sales profile
            sales_entitlements = manager.get_compatible_entitlements(AppType.SALES)
            # Returns: ['Salesforce Access', 'Office 365 License', 'Slack Access', ...]
            
        Note:
            - Compatible entitlements are defined per profile based on business needs
            - These entitlements integrate with the existing config.py settings
            - Only compatible entitlements should be assigned to users in each profile
            - Entitlement assignments may require additional approval workflows
        """
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return profile.compatible_entitlements
    
    def get_compatible_departments(self, app_type: AppType) -> List[str]:
        """Get compatible department names from existing config for a given app type."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return profile.compatible_departments
    
    def get_compatible_groups(self, app_type: AppType) -> List[str]:
        """Get compatible group names from existing config for a given app type."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        return profile.compatible_groups
    
    def get_entitlement_definitions_for_profile(self, app_type: AppType) -> List[Dict[str, Any]]:
        """Get entitlement definitions from existing config that are compatible with the app profile."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        compatible_names = profile.compatible_entitlements
        compatible_definitions = []
        
        for entitlement_def in settings.cli_entitlement_definitions:
            if entitlement_def["name"] in compatible_names:
                compatible_definitions.append(entitlement_def)
        
        return compatible_definitions
    
    def get_department_job_titles_for_profile(self, app_type: AppType) -> List[tuple]:
        """Get department job titles from existing config that are compatible with the app profile."""
        profile = self.get_profile(app_type)
        if not profile:
            return []
        
        compatible_departments = profile.compatible_departments
        compatible_job_titles = []
        
        for dept, titles in settings.cli_department_job_titles:
            if dept in compatible_departments:
                compatible_job_titles.append((dept, titles))
        
        return compatible_job_titles

# Global instance - lazy initialization to avoid circular imports
_app_profile_manager = None

def get_app_profile_manager() -> AppProfileManager:
    """Get the global app profile manager instance."""
    global _app_profile_manager
    if _app_profile_manager is None:
        _app_profile_manager = AppProfileManager()
    return _app_profile_manager

# For backward compatibility
app_profile_manager = get_app_profile_manager() 