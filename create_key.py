#!/usr/bin/env python3
"""
API Key Creation Script

This script creates new API keys for the Prometheus Gateway.
Usage: python create_key.py <owner_name>
"""

import sys
from sqlmodel import Session

from app.database import engine
from app.crud.api_key import create_db_api_key


def main():
    # Check if owner argument is provided
    if len(sys.argv) != 2:
        print("Usage: python create_key.py <owner_name>")
        print("Example: python create_key.py user@example.com")
        sys.exit(1)
    
    # Get owner from command-line argument
    owner = sys.argv[1]
    
    try:
        # Create database session and generate API key
        with Session(engine) as session:
            plaintext_key, db_api_key = create_db_api_key(session, owner)
            
            # Display the generated key (only time it's ever shown)
            print(f"✅ API Key created for owner '{owner}':")
            print(f"   => {plaintext_key}")
            print()
            print("⚠️  IMPORTANT: Save this key securely - it will not be shown again!")
            print(f"   Key ID: {db_api_key.id}")
            print(f"   Created: {db_api_key.created_at}")
            print(f"   Status: {'Active' if db_api_key.is_active else 'Inactive'}")
            
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 