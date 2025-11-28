#!/usr/bin/env python3
"""
Database setup script for Närvarorapportering
Creates database and runs migrations using Python instead of psql
"""
import os
import psycopg
from dotenv import load_dotenv

def setup_database():
    """Setup the database and run migrations"""
    print("Setting up Närvarorapportering database...")
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/alarm')
    print(f"Using database URL: {database_url}")
    
    # Extract database name
    db_name = database_url.split('/')[-1]
    base_url = database_url.rsplit('/', 1)[0] + '/postgres'  # Connect to default postgres db
    
    try:
        # Connect to PostgreSQL server (not the specific database)
        print("Connecting to PostgreSQL server...")
        with psycopg.connect(base_url) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                if cur.fetchone():
                    print(f"Database '{db_name}' already exists")
                else:
                    # Create database
                    print(f"Creating database '{db_name}'...")
                    cur.execute(f"CREATE DATABASE {db_name}")
                    print(f"Database '{db_name}' created successfully")
        
        # Now connect to our specific database and run migrations
        print("Running consolidated migration...")
        with psycopg.connect(database_url) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Run consolidated 001_init_with_data.sql (includes all features)
                print("Running 001_init_with_data.sql (consolidated migration)...")
                with open('migrations/001_init_with_data.sql', 'r', encoding='utf-8') as f:
                    sql = f.read()
                cur.execute(sql)
                print("Complete database schema and data created successfully")
        
        print("\nDatabase setup completed successfully!")
        print(f"Database: {db_name}")
        
    except psycopg.Error as e:
        print(f"Database error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your .env file has correct DATABASE_URL")
        print("3. Make sure the user has permission to create databases")
        return False
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = setup_database()
    if not success:
        exit(1)
