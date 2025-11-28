#!/usr/bin/env python3
"""
Setup script for Närvarorapportering
"""
import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("Setting up Närvarorapportering...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠ Warning: You're not in a virtual environment.")
        print("  Consider running: python -m venv .venv && source .venv/bin/activate")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return
    
    # Check if .env exists
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            print("Creating .env from env.example...")
            with open('env.example', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print("✓ Created .env file")
        else:
            print("⚠ No .env file found. Please create one with your database credentials.")
    
    print("\n✓ Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env with your database credentials")
    print("2. Create PostgreSQL database: createdb narvaro")
    print("3. Run migrations: psql narvaro -f migrations/001_init.sql && psql narvaro -f migrations/002_seed.sql")
    print("4. Start the application: python run.py")

if __name__ == '__main__':
    main()
