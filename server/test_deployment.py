#!/usr/bin/env python3
"""
Test script to verify deployment configuration
Run this before deploying to ensure everything is set up correctly
"""

import os
import sys
import requests
from dotenv import load_dotenv

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    load_dotenv()
    
    required_vars = ['GEMINI_API_KEY', 'MONGO_URI']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🗄️  Testing MongoDB Connection...")
    
    try:
        from database import client
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_gemini_api():
    """Test Gemini API connection"""
    print("\n🤖 Testing Gemini API...")
    
    try:
        import google.generativeai as genai
        from feedback_processor import model
        
        if model is None:
            print("❌ Gemini model not configured")
            return False
        
        # Test with a simple prompt
        response = model.generate_content("Hello, this is a test.")
        if response.text:
            print("✅ Gemini API connection successful")
            return True
        else:
            print("❌ Gemini API returned empty response")
            return False
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

def test_flask_app():
    """Test Flask app configuration"""
    print("\n🌐 Testing Flask App Configuration...")
    
    try:
        from app import app
        
        # Test CORS configuration
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Flask app and health endpoint working")
                return True
            else:
                print(f"❌ Health endpoint returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_dependencies():
    """Test if all required packages are installed"""
    print("\n📦 Testing Dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'pandas',
        'numpy',
        'matplotlib',
        'fpdf',
        'google.generativeai',
        'openpyxl',
        'pymongo',
        'python_dotenv',
        'gunicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def main():
    """Run all tests"""
    print("🚀 Deployment Configuration Test")
    print("=" * 40)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Dependencies", test_dependencies),
        ("MongoDB Connection", test_mongodb_connection),
        ("Gemini API", test_gemini_api),
        ("Flask App", test_flask_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Your application is ready for deployment.")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Connect your repository to Render")
        print("3. Set environment variables in Render dashboard")
        print("4. Deploy!")
    else:
        print("⚠️  Some tests failed. Please fix the issues before deploying.")
        print("\nCommon fixes:")
        print("- Set GEMINI_API_KEY environment variable")
        print("- Set MONGO_URI environment variable")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Check MongoDB Atlas connection")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
