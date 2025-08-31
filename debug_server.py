#!/usr/bin/env python3
"""
Debug script for Recipe Recommender Web App
Tests server startup and basic functionality
"""

import sys
import os
import requests
import time
import threading
from backend.app import app, init_database

def test_server_startup():
    """Test if the Flask server starts without errors"""
    print("🔧 Testing server startup...")
    
    try:
        # Test database initialization
        print("📊 Testing database initialization...")
        init_database()
        print("✅ Database initialization successful")
        
        # Test Flask app creation
        print("🌐 Testing Flask app...")
        if app:
            print("✅ Flask app created successfully")
            print(f"📍 App configuration:")
            print(f"   - Template folder: {app.template_folder}")
            print(f"   - Static folder: {app.static_folder}")
            print(f"   - Secret key configured: {'Yes' if app.secret_key else 'No'}")
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False
    
    return True

def test_ai_integration():
    """Test AI assistant integration"""
    print("\n🤖 Testing AI assistant integration...")
    
    try:
        from backend.ai_assistant import get_ai_assistant, get_image_generator
        
        # Test AI assistant creation
        ai_assistant = get_ai_assistant()
        print("✅ AI assistant created successfully")
        
        # Test image generator
        image_generator = get_image_generator()
        print("✅ Image generator created successfully")
        
        # Check OpenAI API key configuration
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your-openai-api-key-here':
            print("✅ OpenAI API key is configured")
        else:
            print("⚠️  OpenAI API key not configured - AI features will not work")
            print("   Set OPENAI_API_KEY environment variable to enable AI features")
        
    except Exception as e:
        print(f"❌ AI integration test failed: {e}")
        return False
    
    return True

def start_test_server():
    """Start Flask server in a thread for testing"""
    def run_server():
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Give server time to start
    return server_thread

def test_api_endpoints():
    """Test basic API endpoints"""
    print("\n🔍 Testing API endpoints...")
    
    base_url = "http://127.0.0.1:5000"
    
    endpoints_to_test = [
        ("/api/recipes", "GET", "Get all recipes"),
        ("/api/countries", "GET", "Get countries"),
        ("/api/cuisines", "GET", "Get cuisines"),
        ("/api/surprise", "GET", "Get surprise recipes"),
    ]
    
    for endpoint, method, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: {len(data) if isinstance(data, list) else 'OK'}")
            else:
                print(f"⚠️  {description}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {description}: Connection failed")
        except Exception as e:
            print(f"❌ {description}: {e}")

def check_frontend_files():
    """Check if frontend files exist and are properly structured"""
    print("\n📁 Checking frontend files...")
    
    required_files = [
        "templates/index.html",
        "templates/login.html", 
        "templates/signup.html",
        "static/css/style.css",
        "static/css/auth.css",
        "static/js/app.js",
        "static/js/auth.js"
    ]
    
    for file_path in required_files:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} - Missing")

def check_database():
    """Check database tables and data"""
    print("\n🗄️  Checking database...")
    
    try:
        import sqlite3
        from backend.app import DB_PATH
        
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            
            # Check tables
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            print(f"✅ Database file exists with {len(tables)} tables:")
            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
                print(f"   - {table[0]}: {count} records")
            
            conn.close()
        else:
            print(f"❌ Database file not found at: {DB_PATH}")
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")

def main():
    """Main debug function"""
    print("🚀 Recipe Recommender Web App Debug Tool")
    print("=" * 50)
    
    # Test server startup components
    if not test_server_startup():
        print("\n❌ Server startup tests failed")
        return
    
    # Test AI integration
    if not test_ai_integration():
        print("\n⚠️  AI integration has issues")
    
    # Check frontend files
    check_frontend_files()
    
    # Check database
    check_database()
    
    # Start test server
    print("\n🌐 Starting test server...")
    try:
        server_thread = start_test_server()
        print("✅ Test server started on http://127.0.0.1:5000")
        
        # Test API endpoints
        test_api_endpoints()
        
        print("\n🎉 Debug complete!")
        print("📍 You can now visit http://127.0.0.1:5000 to test the web app")
        print("🔧 To run the full server, use: python backend/app.py")
        
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")

if __name__ == "__main__":
    main()
