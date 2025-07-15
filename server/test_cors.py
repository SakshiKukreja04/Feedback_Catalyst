#!/usr/bin/env python3
"""
Test script to verify CORS is working
"""

import requests
import json

def test_cors():
    base_url = "http://localhost:5001"
    
    print("🧪 Testing CORS Configuration...")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    try:
        response = requests.get(f"{base_url}/test")
        print(f"✅ Server connectivity: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on port 5001")
        return False
    
    # Test 2: CORS headers on test endpoint
    try:
        response = requests.get(f"{base_url}/test")
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        print(f"✅ CORS header on /test: {cors_header}")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
    
    # Test 3: OPTIONS preflight request
    try:
        response = requests.options(f"{base_url}/upload")
        print(f"✅ OPTIONS preflight: {response.status_code}")
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        print(f"CORS headers: {cors_headers}")
    except Exception as e:
        print(f"❌ OPTIONS test failed: {e}")
    
    # Test 4: Simulate frontend request
    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{base_url}/test", headers=headers)
        print(f"✅ Frontend simulation: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ Frontend simulation failed: {e}")
    
    print("=" * 50)
    print("🎯 CORS Test Complete!")
    return True

if __name__ == "__main__":
    test_cors() 