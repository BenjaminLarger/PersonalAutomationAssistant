#!/usr/bin/env python3
"""
Test script to verify the setup and basic functionality
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    print("🧪 Testing Environment Setup")
    print("=" * 40)
    
    # Test .env file
    if os.path.exists('.env'):
        print("✅ .env file exists")
        load_dotenv()
        
        required_vars = [
            'OPENAI_API_KEY',
            'GOOGLE_CLIENT_ID', 
            'GOOGLE_CLIENT_SECRET',
            'CALDAV_URL',
            'CALDAV_USERNAME',
            'CALDAV_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ All required environment variables are set")
    else:
        print("❌ .env file not found")
        return False
    
    return len(missing_vars) == 0

def test_imports():
    print("\n🧪 Testing Python Imports")
    print("=" * 40)
    
    modules = [
        'fastapi',
        'uvicorn', 
        'langchain',
        'openai',
        'google',
        'pydantic',
        'caldav',
        'icalendar'
    ]
    
    failed_imports = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def test_api_connection():
    print("\n🧪 Testing API Connections")
    print("=" * 40)
    
    # Test OpenAI
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            print("✅ OpenAI API key configured")
        else:
            print("⚠️  OpenAI API key not configured")
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
    
    # Test Calendar manager
    try:
        from agents.calendar_manager import CalendarManager
        cal_manager = CalendarManager()
        test_result = cal_manager.test_connection()
        if test_result['connected']:
            print("✅ Calendar connection successful")
        else:
            print(f"⚠️  Calendar connection: {test_result['message']}")
    except Exception as e:
        print(f"❌ Calendar test failed: {e}")

def main():
    print("🚀 Personal Automation Assistant - Setup Test")
    print("=" * 50)
    
    env_ok = test_environment()
    imports_ok = test_imports()
    
    if env_ok and imports_ok:
        test_api_connection()
        print("\n🎉 Basic setup verification completed!")
        print("\n📋 Next steps:")
        print("1. Start the server: python main.py")
        print("2. Open http://localhost:8000 in your browser")
        print("3. Label some emails with 'meetings' in Gmail")
        print("4. Click 'Process Meeting Emails' to test the full workflow")
    else:
        print("\n❌ Setup issues detected. Please resolve them before proceeding.")
        if not env_ok:
            print("- Configure your .env file with valid API keys")
        if not imports_ok:
            print("- Install missing Python packages: pip install -r requirements.txt")

if __name__ == "__main__":
    main()