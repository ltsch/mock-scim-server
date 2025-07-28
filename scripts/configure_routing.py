#!/usr/bin/env python3
"""
Routing Configuration Script

This script demonstrates how to configure different routing strategies
for the SCIM server to support various SCIM clients.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.routing_config import RoutingStrategy, configure_routing, get_compatibility_info
from scim_server.server_context import ServerIdSource, configure_server_id_source
from loguru import logger

def print_routing_info():
    """Print current routing configuration information."""
    compatibility_info = get_compatibility_info()
    
    print("\n" + "="*60)
    print("SCIM SERVER ROUTING CONFIGURATION")
    print("="*60)
    
    print(f"\nCurrent Strategy: {compatibility_info['strategy']}")
    print(f"Enabled Strategies: {', '.join(compatibility_info['enabled_strategies'])}")
    
    print("\n" + "-"*40)
    print("CLIENT COMPATIBILITY")
    print("-"*40)
    
    for method in compatibility_info['client_compatibility']:
        print(f"\nMethod: {method['method'].upper()}")
        print(f"Description: {method['description']}")
        print(f"Example: {method['example']}")
        print(f"Limitations: {method['limitations']}")
    
    print("\n" + "-"*40)
    print("RECOMMENDATIONS")
    print("-"*40)
    print("• For standard SCIM clients: Use PATH_PARAM strategy")
    print("• For Okta integration: Use HYBRID strategy")
    print("• For custom clients: Use QUERY_PARAM strategy")
    print("• For maximum compatibility: Use HYBRID strategy")

def configure_for_scim_clients():
    """Configure routing for standard SCIM clients."""
    print("\nConfiguring for standard SCIM clients...")
    configure_routing(RoutingStrategy.PATH_PARAM)
    print("✓ Configured for PATH_PARAM strategy")
    print("✓ Best compatibility with standard SCIM clients")
    print("✓ URLs: /scim-identifier/{server_id}/scim/v2/Users")

def configure_for_okta():
    """Configure routing for Okta integration."""
    print("\nConfiguring for Okta integration...")
    configure_routing(RoutingStrategy.HYBRID)
    print("✓ Configured for HYBRID strategy")
    print("✓ Supports all routing methods")
    print("✓ Maximum compatibility with Okta")

def configure_for_custom_clients():
    """Configure routing for custom SCIM clients."""
    print("\nConfiguring for custom SCIM clients...")
    configure_routing(RoutingStrategy.QUERY_PARAM)
    print("✓ Configured for QUERY_PARAM strategy")
    print("✓ Simple URL structure")
    print("✓ URLs: /scim/v2/Users?serverID={server_id}")

def configure_for_headers():
    """Configure routing using HTTP headers."""
    print("\nConfiguring for header-based routing...")
    configure_routing(RoutingStrategy.HEADER)
    print("✓ Configured for HEADER strategy")
    print("✓ Clean URLs with X-Server-ID header")
    print("✓ URLs: /scim/v2/Users (with X-Server-ID header)")

def main():
    """Main function to demonstrate routing configuration."""
    print("SCIM Server Routing Configuration Tool")
    print("=====================================")
    
    while True:
        print("\nAvailable configurations:")
        print("1. Standard SCIM clients (PATH_PARAM)")
        print("2. Okta integration (HYBRID)")
        print("3. Custom clients (QUERY_PARAM)")
        print("4. Header-based routing (HEADER)")
        print("5. Show current configuration")
        print("6. Exit")
        
        choice = input("\nSelect configuration (1-6): ").strip()
        
        if choice == "1":
            configure_for_scim_clients()
        elif choice == "2":
            configure_for_okta()
        elif choice == "3":
            configure_for_custom_clients()
        elif choice == "4":
            configure_for_headers()
        elif choice == "5":
            print_routing_info()
        elif choice == "6":
            print("\nExiting...")
            break
        else:
            print("Invalid choice. Please select 1-6.")
        
        if choice in ["1", "2", "3", "4"]:
            print_routing_info()

if __name__ == "__main__":
    main() 