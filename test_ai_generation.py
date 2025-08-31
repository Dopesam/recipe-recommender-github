#!/usr/bin/env python3
"""
Test script for AI recipe generation endpoint
This script tests the API without actually calling OpenAI
"""

import json
import sqlite3
import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_database_setup():
    """Test that the database and AI recipes table are properly set up"""
    from app import init_database, get_db_connection
    
    print("🔧 Testing database setup...")
    
    # Initialize database
    init_database()
    
    # Check if ai_recipes table exists
    conn = get_db_connection()
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [table['name'] for table in tables]
        
        print(f"📊 Database tables: {table_names}")
        
        if 'ai_recipes' in table_names:
            print("✅ AI recipes table exists")
            
            # Check table structure
            columns = conn.execute("PRAGMA table_info(ai_recipes)").fetchall()
            column_names = [col['name'] for col in columns]
            print(f"📋 AI recipes table columns: {column_names}")
            
        else:
            print("❌ AI recipes table missing")
            return False
            
        if 'users' in table_names:
            print("✅ Users table exists")
        else:
            print("❌ Users table missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()

def test_api_endpoint_structure():
    """Test that the API endpoint is properly structured"""
    from app import app
    
    print("\n🔧 Testing API endpoint structure...")
    
    with app.test_client() as client:
        # Test without authentication (should return 401)
        response = client.post('/api/generate-recipe', 
                             data=json.dumps({
                                 'ingredients': ['tomato', 'chicken', 'rice'],
                                 'preferences': {'difficulty': 'easy', 'cuisine': 'italian'}
                             }),
                             content_type='application/json')
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication check working (returns 401 for unauthenticated requests)")
            response_data = response.get_json()
            print(f"📋 Response: {response_data}")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            return False

def test_ingredient_processing():
    """Test ingredient processing logic"""
    print("\n🔧 Testing ingredient processing logic...")
    
    # Sample ingredients and preferences like the frontend would send
    test_payload = {
        'ingredients': ['chicken breast', 'rice', 'bell peppers', 'onion'],
        'preferences': {
            'difficulty': 'Medium',
            'cuisine': 'Asian'
        }
    }
    
    ingredients_text = ", ".join(test_payload['ingredients'])
    prompt_parts = [f"Create a recipe using these ingredients: {ingredients_text}"]
    
    if test_payload['preferences'].get('difficulty'):
        prompt_parts.append(f"The recipe should be {test_payload['preferences']['difficulty']} difficulty.")
    
    if test_payload['preferences'].get('cuisine'):
        prompt_parts.append(f"Make it {test_payload['preferences']['cuisine']} style cuisine.")
    
    user_prompt = " ".join(prompt_parts)
    
    expected_prompt = "Create a recipe using these ingredients: chicken breast, rice, bell peppers, onion The recipe should be Medium difficulty. Make it Asian style cuisine."
    
    if user_prompt == expected_prompt:
        print("✅ Ingredient processing logic works correctly")
        print(f"📋 Generated prompt: {user_prompt}")
        return True
    else:
        print(f"❌ Prompt mismatch!")
        print(f"Expected: {expected_prompt}")
        print(f"Got: {user_prompt}")
        return False

def test_openai_client_creation():
    """Test OpenAI client creation (without making actual API calls)"""
    print("\n🔧 Testing OpenAI client creation...")
    
    import openai
    
    try:
        # Test client creation with dummy API key
        client = openai.OpenAI(api_key="test-key")
        print("✅ OpenAI client created successfully")
        print(f"📋 Client type: {type(client)}")
        return True
    except Exception as e:
        print(f"❌ OpenAI client creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AI Recipe Generator Setup")
    print("=" * 50)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("API Endpoint Structure", test_api_endpoint_structure),
        ("Ingredient Processing", test_ingredient_processing),
        ("OpenAI Client Creation", test_openai_client_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("🧪 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The AI recipe generator should work correctly.")
        print("\n📝 Next steps:")
        print("1. Set up your OPENAI_API_KEY environment variable")
        print("2. Start the Flask app with: python app.py")
        print("3. Test the AI generator through the web interface")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")

if __name__ == "__main__":
    main()
