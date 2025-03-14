#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_status(message, is_ok=True):
    """Print a status message with colored output"""
    if is_ok:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

def main():
    print("Environment File Check Script")
    print("-----------------------------")
    
    # Try to find and load .env file
    env_files = [
        os.path.join(os.getcwd(), "backend", ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(Path(__file__).resolve().parent, "backend", ".env"),
    ]
    
    env_loaded = False
    env_file_path = None
    
    for env_path in env_files:
        if os.path.exists(env_path):
            print_status(f"Found .env file at: {env_path}")
            load_dotenv(dotenv_path=env_path, override=True)
            env_loaded = True
            env_file_path = env_path
            break
    
    if not env_loaded:
        print_status("Could not find .env file", False)
        return
    
    # Check for required variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "NEO4J_URI",
        "NEO4J_USER", 
        "NEO4J_PASSWORD"
    ]
    
    print("\nChecking required environment variables:")
    all_vars_present = True
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            masked_value = value[:5] + "..." + value[-5:] if len(value) > 12 else "***"
            print_status(f"{var}: {masked_value}")
        else:
            print_status(f"{var}: Not set", False)
            all_vars_present = False
    
    # Print sample code to manually set variables
    if not all_vars_present:
        print("\nSample code to manually set variables:\n")
        print("import os")
        print("# Add these lines to your script:")
        for var in required_vars:
            if not os.environ.get(var):
                print(f'os.environ["${var}"] = "YOUR_{var}_VALUE"')
    
    # Check file contents without exposing sensitive data
    if env_file_path:
        print("\nChecking .env file content structure:")
        try:
            with open(env_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if '=' in line and not line.strip().startswith('#'):
                        key = line.split('=')[0].strip()
                        print_status(f"Found key in file: {key}")
        except Exception as e:
            print_status(f"Error reading .env file: {e}", False)

if __name__ == "__main__":
    main() 