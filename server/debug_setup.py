#!/usr/bin/env python3
"""
Comprehensive debugging script for Flask API with MongoDB Atlas
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

def check_environment():
    """Check environment variables and .env file"""
    print("🔍 Checking Environment Setup...")
    print("=" * 50)
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        load_dotenv()
    else:
        print("❌ .env file not found")
        print("   Please create a .env file with your MongoDB Atlas URI")
        return False
    
    # Check MongoDB URI
    mongo_uri = os.getenv('MONGODB_URI')
    if mongo_uri:
        print("✅ MONGODB_URI found in environment")
        # Mask the URI for security
        masked_uri = mongo_uri.split('@')[0] + '@***' if '@' in mongo_uri else '***'
        print(f"   URI: {masked_uri}")
    else:
        print("❌ MONGODB_URI not found in environment")
        print("   Please add MONGODB_URI to your .env file")
        return False
    
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking Dependencies...")
    print("=" * 50)
    
    required_packages = [
        'flask', 'flask_cors', 'pandas', 'pymongo', 
        'python-dotenv', 'openpyxl', 'matplotlib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    print("\n🗄️  Testing MongoDB Connection...")
    print("=" * 50)
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        mongo_uri = os.getenv('MONGODB_URI')
        if not mongo_uri:
            print("❌ MONGODB_URI not available")
            return False
        
        print("Attempting to connect to MongoDB Atlas...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful!")
        
        # Test database access
        db = client.get_database()
        collection = db.parsedFeedback
        print("✅ Database and collection access successful!")
        
        client.close()
        return True
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   Please check your connection string and network")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"❌ MongoDB server selection timeout: {e}")
        print("   Please check your MongoDB Atlas cluster status")
        return False
    except Exception as e:
        print(f"❌ Unexpected MongoDB error: {e}")
        return False

def test_flask_server():
    """Test if Flask server is running and responding"""
    print("\n🌐 Testing Flask Server...")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:5001/test', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Flask server is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   MongoDB Connected: {data.get('mongodb_connected')}")
            return True
        else:
            print(f"❌ Flask server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Flask server is not running")
        print("   Please start the server with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error testing Flask server: {e}")
        return False

def test_cors():
    """Test CORS configuration"""
    print("\n🔒 Testing CORS Configuration...")
    print("=" * 50)
    
    try:
        # Test OPTIONS preflight request
        response = requests.options('http://localhost:5001/upload')
        print(f"✅ OPTIONS request: {response.status_code}")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"   ✅ {header}: {value}")
            else:
                print(f"   ❌ {header}: Not found")
        
        return True
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    print("\n📁 Testing File Upload...")
    print("=" * 50)
    
    try:
        # Create a test CSV file
        test_file_content = "Name,Rating,Feedback\nJohn,5,Great course\nJane,4,Good content"
        
        files = {'file': ('test.csv', test_file_content, 'text/csv')}
        response = requests.post('http://localhost:5001/upload', files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ File upload successful!")
            print(f"   Filename: {data.get('filename')}")
            print(f"   ID: {data.get('id')}")
            print(f"   Columns: {data.get('columns')}")
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Flask API Debug Setup")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", check_environment),
        ("Dependencies", check_dependencies),
        ("MongoDB Connection", test_mongodb_connection),
        ("Flask Server", test_flask_server),
        ("CORS Configuration", test_cors),
        ("File Upload", test_file_upload)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
        if not results[0][1]:  # Environment failed
            print("\n🔧 Quick Fix: Create a .env file with:")
            print("MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority")
        
        if not results[2][1]:  # MongoDB failed
            print("\n🔧 Quick Fix: Check your MongoDB Atlas connection string and network access")
        
        if not results[3][1]:  # Flask server failed
            print("\n🔧 Quick Fix: Start the server with: python app.py")

if __name__ == "__main__":
    main() 