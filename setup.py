#!/usr/bin/env python3
"""
Setup script for Personal Automation Assistant
Creates virtual environment and installs dependencies
"""

import subprocess
import sys
import os

def run_command(command, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    print("🚀 Setting up Personal Automation Assistant")
    print("=" * 50)
    
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Already in virtual environment")
        venv_python = sys.executable
    else:
        # Create virtual environment
        if not os.path.exists('venv'):
            run_command('python3 -m venv venv', 'Creating virtual environment')
        
        # Determine the python executable path
        if os.name == 'nt':  # Windows
            venv_python = 'venv\\Scripts\\python.exe'
        else:  # Unix/Linux/MacOS
            venv_python = 'venv/bin/python'
    
    # Install dependencies
    run_command(f'{venv_python} -m pip install --upgrade pip', 'Upgrading pip')
    run_command(f'{venv_python} -m pip install -r requirements.txt', 'Installing dependencies')
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        with open('.env.example', 'r') as example:
            with open('.env', 'w') as env_file:
                env_file.write(example.read())
        print("✅ .env file created. Please update it with your actual API keys and credentials.")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Update .env file with your API keys and credentials")
    print("2. Set up Google OAuth credentials")
    print("3. Configure Apple Calendar CalDAV settings")
    
    print("4. Run the application: python main.py")
    print("\n💡 See README.md for detailed setup instructions")

if __name__ == "__main__":
    main()