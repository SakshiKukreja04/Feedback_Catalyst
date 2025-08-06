#!/usr/bin/env python3
"""
Test script to verify CORS configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test CORS configuration
frontend_url = os.environ.get("VITE_FRONTEND_BASE_URL")
print(f"Frontend URL from environment: {frontend_url}")

if frontend_url:
    print(f"✅ CORS will be configured for: {frontend_url}")
else:
    print("⚠️  No VITE_FRONTEND_BASE_URL found, using '*' for all origins")

# Test other environment variables
print(f"PORT: {os.environ.get('PORT', '5001')}")
print(f"NODE_ENV: {os.environ.get('NODE_ENV', 'development')}")
