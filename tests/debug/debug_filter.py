#!/usr/bin/env python3
"""
Debug script to test SCIM filtering
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scim_server.database import SessionLocal
from scim_server.utils import parse_scim_filter
from scim_server.crud import get_users

def test_filter():
    """Test the filter parsing and database query."""
    db = SessionLocal()
    
    try:
        # Test filter parsing
        filter_query = 'userName eq "testuser@example.com"'
        print(f"Testing filter: {filter_query}")
        
        parsed = parse_scim_filter(filter_query)
        print(f"Parsed result: {parsed}")
        
        # Test database query
        users = get_users(db, filter_query=filter_query)
        print(f"Query returned {len(users)} users")
        
        for user in users:
            print(f"  - {user.user_name} ({user.display_name})")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_filter() 