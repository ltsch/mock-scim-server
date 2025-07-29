#!/bin/bash

# Generate Test Data Script for SCIM Server Profiles
# This script creates test data for each profile with 50 users, 10 groups, and 10 entitlements

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OUTPUT_DIR="test_data"
PROFILES=("hr" "it" "sales" "marketing" "finance" "legal" "operations" "security" "customer_success" "research" "engineering" "product" "support")
USERS_PER_PROFILE=50
GROUPS_PER_PROFILE=10
ENTITLEMENTS_PER_PROFILE=10

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if CLI is available
check_cli() {
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    if ! python -c "import sys; sys.path.append('.'); from scripts.scim_cli import SCIMCLI" &> /dev/null; then
        print_error "SCIM CLI is not available. Make sure you're in the correct directory."
        exit 1
    fi
}

# Function to create output directory
create_output_dir() {
    if [ ! -d "$OUTPUT_DIR" ]; then
        print_status "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
}

# Function to generate test data for a profile
generate_profile_data() {
    local profile=$1
    local server_id="${profile}_test_server_$(date +%s)"
    local output_file="$OUTPUT_DIR/${profile}_test_data.json"
    
    print_status "Generating test data for profile: $profile"
    print_status "Server ID: $server_id"
    print_status "Output file: $output_file"
    
    # Create virtual server with the profile
    print_status "Creating virtual server with profile: $profile"
    
    # Use Python to call the CLI with JSON output
    python3 -c "
import sys
import json
from datetime import datetime
from scripts.scim_cli import SCIMCLI
from scim_server.database import get_db
from scim_server.models import User, Group, Entitlement, UserGroup, UserEntitlement

profile_name = '$profile'
server_id = '$server_id'
output_file = '$output_file'
users_count = $USERS_PER_PROFILE
groups_count = $GROUPS_PER_PROFILE
entitlements_count = $ENTITLEMENTS_PER_PROFILE

try:
    cli = SCIMCLI()
    
    # Create virtual server with profile
    result = cli.create_virtual_server(
        server_id=server_id,
        users=users_count,
        groups=groups_count,
        entitlements=entitlements_count,
        app_profile=profile_name
    )
    
    # Get server statistics
    stats_result = cli.get_server_stats(server_id)
    
    # Get server configuration
    config_result = cli.get_server_config(server_id)
    
    # Get database session to fetch actual data
    db = next(get_db())
    
    try:
        # Fetch users with all attributes
        users = db.query(User).filter(User.server_id == server_id).all()
        users_data = []
        for user in users:
            user_dict = {}
            for column in user.__table__.columns:
                value = getattr(user, column.name)
                if isinstance(value, datetime):
                    user_dict[column.name] = value.isoformat() if value else None
                else:
                    user_dict[column.name] = value
            
            # Get user's entitlements
            user_entitlements = db.query(UserEntitlement).filter(UserEntitlement.user_id == user.id).all()
            user_dict['entitlements'] = []
            for user_entitlement in user_entitlements:
                entitlement = db.query(Entitlement).filter(Entitlement.id == user_entitlement.entitlement_id).first()
                if entitlement:
                    user_dict['entitlements'].append({
                        'id': entitlement.id,
                        'scim_id': entitlement.scim_id,
                        'display_name': entitlement.display_name,
                        'type': entitlement.type,
                        'description': entitlement.description,
                        'entitlement_type': entitlement.entitlement_type,
                        'multi_valued': entitlement.multi_valued
                    })
            
            # Get user's groups
            user_groups = db.query(UserGroup).filter(UserGroup.user_id == user.id).all()
            user_dict['groups'] = []
            for user_group in user_groups:
                group = db.query(Group).filter(Group.id == user_group.group_id).first()
                if group:
                    user_dict['groups'].append({
                        'id': group.id,
                        'scim_id': group.scim_id,
                        'display_name': group.display_name,
                        'description': group.description
                    })
            
            users_data.append(user_dict)
        
        # Fetch groups with all attributes
        groups = db.query(Group).filter(Group.server_id == server_id).all()
        groups_data = []
        for group in groups:
            group_dict = {}
            for column in group.__table__.columns:
                value = getattr(group, column.name)
                if isinstance(value, datetime):
                    group_dict[column.name] = value.isoformat() if value else None
                else:
                    group_dict[column.name] = value
            
            # Get group members
            group_dict['members'] = []
            user_groups = db.query(UserGroup).filter(UserGroup.group_id == group.id).all()
            for user_group in user_groups:
                user = db.query(User).filter(User.id == user_group.user_id).first()
                if user:
                    group_dict['members'].append({
                        'user_id': user.id,
                        'user_name': user.user_name,
                        'display_name': user.display_name
                    })
            groups_data.append(group_dict)
        
        # Fetch entitlements with all attributes
        entitlements = db.query(Entitlement).filter(Entitlement.server_id == server_id).all()
        entitlements_data = []
        for entitlement in entitlements:
            entitlement_dict = {}
            for column in entitlement.__table__.columns:
                value = getattr(entitlement, column.name)
                if isinstance(value, datetime):
                    entitlement_dict[column.name] = value.isoformat() if value else None
                else:
                    entitlement_dict[column.name] = value
            
            # Get entitlement assignments
            entitlement_dict['assigned_users'] = []
            user_entitlements = db.query(UserEntitlement).filter(UserEntitlement.entitlement_id == entitlement.id).all()
            for user_entitlement in user_entitlements:
                user = db.query(User).filter(User.id == user_entitlement.user_id).first()
                if user:
                    entitlement_dict['assigned_users'].append({
                        'user_id': user.id,
                        'user_name': user.user_name,
                        'display_name': user.display_name
                    })
            entitlements_data.append(entitlement_dict)
        
        # Combine all data
        test_data = {
            'profile': profile_name,
            'server_id': server_id,
            'creation_result': result,
            'statistics': stats_result,
            'server_config': config_result,
            'users': users_data,
            'groups': groups_data,
            'entitlements': entitlements_data,
            'metadata': {
                'users_count': users_count,
                'groups_count': groups_count,
                'entitlements_count': entitlements_count,
                'generated_at': '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
            }
        }
        
        # Write to JSON file
        with open(output_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f'Successfully generated test data for {profile_name} profile')
        print(f'Server created: {result.get(\"success\", False)}')
        print(f'Users: {len(users_data)}')
        print(f'Groups: {len(groups_data)}')
        print(f'Entitlements: {len(entitlements_data)}')
        
    finally:
        # Close database session
        db.close()
    
except Exception as e:
    print(f'Error generating data for {profile_name}: {str(e)}')
    raise e
"
    
    if [ $? -eq 0 ]; then
        print_status "Successfully generated test data for $profile profile"
        print_status "Output saved to: $output_file"
    else
        print_error "Failed to generate test data for $profile profile"
        return 1
    fi
}

# Function to generate summary report
generate_summary_report() {
    local summary_file="$OUTPUT_DIR/test_data_summary.json"
    
    print_status "Generating summary report..."
    
    python3 -c "
import sys
import json
import os
from datetime import datetime

summary = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'profiles_generated': [],
    'total_users': 0,
    'total_groups': 0,
    'total_entitlements': 0,
    'output_directory': '$OUTPUT_DIR'
}

profiles = ['hr', 'it', 'sales', 'marketing', 'finance', 'legal', 'operations', 'security', 'customer_success', 'research', 'engineering', 'product', 'support']
total_users = 0
total_groups = 0
total_entitlements = 0

for profile in profiles:
    output_file = f'$OUTPUT_DIR/{profile}_test_data.json'
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            users_count = len(data.get('users', []))
            groups_count = len(data.get('groups', []))
            entitlements_count = len(data.get('entitlements', []))
            
            profile_summary = {
                'profile': profile,
                'server_id': data.get('server_id'),
                'users_count': users_count,
                'groups_count': groups_count,
                'entitlements_count': entitlements_count,
                'output_file': f'{profile}_test_data.json'
            }
            
            summary['profiles_generated'].append(profile_summary)
            total_users += users_count
            total_groups += groups_count
            total_entitlements += entitlements_count
            
        except Exception as e:
            print(f'Error reading {output_file}: {str(e)}')
    else:
        print(f'Warning: {output_file} not found')

summary['total_users'] = total_users
summary['total_groups'] = total_groups
summary['total_entitlements'] = total_entitlements

with open('$summary_file', 'w') as f:
    json.dump(summary, f, indent=2)

print(f'Summary report generated: $summary_file')
print(f'Total profiles: {len(summary[\"profiles_generated\"])}')
print(f'Total users: {total_users}')
print(f'Total groups: {total_groups}')
print(f'Total entitlements: {total_entitlements}')
"
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -p, --profile NAME  Generate data for specific profile only"
    echo "  -o, --output DIR    Output directory (default: test_data)"
    echo "  -u, --users N       Number of users per profile (default: 50)"
    echo "  -g, --groups N      Number of groups per profile (default: 10)"
    echo "  -e, --entitlements N Number of entitlements per profile (default: 10)"
    echo ""
    echo "Available profiles:"
    for profile in "${PROFILES[@]}"; do
        echo "  - $profile"
    done
    echo ""
    echo "Examples:"
    echo "  $0                    # Generate data for all profiles"
    echo "  $0 -p hr             # Generate data for HR profile only"
    echo "  $0 -o my_data -u 25  # Custom output dir and user count"
}

# Parse command line arguments
SPECIFIC_PROFILE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -p|--profile)
            SPECIFIC_PROFILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -u|--users)
            USERS_PER_PROFILE="$2"
            shift 2
            ;;
        -g|--groups)
            GROUPS_PER_PROFILE="$2"
            shift 2
            ;;
        -e|--entitlements)
            ENTITLEMENTS_PER_PROFILE="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header "SCIM Server Test Data Generator"
    
    print_status "Configuration:"
    print_status "  Users per profile: $USERS_PER_PROFILE"
    print_status "  Groups per profile: $GROUPS_PER_PROFILE"
    print_status "  Entitlements per profile: $ENTITLEMENTS_PER_PROFILE"
    print_status "  Output directory: $OUTPUT_DIR"
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_cli
    
    # Create output directory
    create_output_dir
    
    # Determine which profiles to process
    if [ -n "$SPECIFIC_PROFILE" ]; then
        # Validate specific profile
        if [[ " ${PROFILES[@]} " =~ " ${SPECIFIC_PROFILE} " ]]; then
            PROFILES_TO_PROCESS=("$SPECIFIC_PROFILE")
            print_status "Generating data for specific profile: $SPECIFIC_PROFILE"
        else
            print_error "Invalid profile: $SPECIFIC_PROFILE"
            echo "Available profiles: ${PROFILES[*]}"
            exit 1
        fi
    else
        PROFILES_TO_PROCESS=("${PROFILES[@]}")
        print_status "Generating data for all profiles: ${PROFILES[*]}"
    fi
    
    # Generate data for each profile
    local success_count=0
    local total_count=${#PROFILES_TO_PROCESS[@]}
    
    for profile in "${PROFILES_TO_PROCESS[@]}"; do
        print_header "Processing Profile: $profile"
        
        if generate_profile_data "$profile"; then
            ((success_count++))
        else
            print_warning "Failed to generate data for $profile, continuing with next profile..."
        fi
        
        echo ""  # Add spacing between profiles
    done
    
    # Generate summary report
    print_header "Generating Summary Report"
    generate_summary_report
    
    # Final status
    print_header "Generation Complete"
    print_status "Successfully generated data for $success_count out of $total_count profiles"
    print_status "Output directory: $OUTPUT_DIR"
    print_status "Summary report: $OUTPUT_DIR/test_data_summary.json"
    
    if [ $success_count -eq $total_count ]; then
        print_status "All profiles generated successfully! 🎉"
    else
        print_warning "Some profiles failed to generate. Check the output above for details."
        exit 1
    fi
}

# Run main function
main "$@" 