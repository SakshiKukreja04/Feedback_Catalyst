#!/usr/bin/env python3
"""
Final deployment check script
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_files():
    """Check if all required files exist"""
    print("📁 Checking required files...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'gunicorn.conf.py',
        'test_cors.py',
        'test_memory.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_environment():
    """Check environment variables"""
    print("\n🌍 Checking environment variables...")
    
    # Check if VITE_FRONTEND_BASE_URL is set
    frontend_url = os.environ.get("VITE_FRONTEND_BASE_URL")
    if frontend_url:
        print(f"   ✅ VITE_FRONTEND_BASE_URL: {frontend_url}")
    else:
        print("   ⚠️  VITE_FRONTEND_BASE_URL: Not set (will use '*' for CORS)")
    
    # Check PORT
    port = os.environ.get('PORT', '5001')
    print(f"   ✅ PORT: {port}")
    
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'pandas',
        'psutil',
        'gunicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_cors_config():
    """Check CORS configuration"""
    print("\n🌐 Checking CORS configuration...")
    
    # Read app.py to check CORS setup
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'VITE_FRONTEND_BASE_URL' in content:
            print("   ✅ CORS uses environment variable")
        else:
            print("   ❌ CORS not configured with environment variable")
            return False
            
        if 'log_memory_usage' in content:
            print("   ✅ Memory monitoring enabled")
        else:
            print("   ❌ Memory monitoring not found")
            return False
            
        return True
    except FileNotFoundError:
        print("   ❌ app.py not found")
        return False

def main():
    """Main check function"""
    print("🚀 Final Deployment Check")
    print("=" * 40)
    
    all_checks_passed = True
    
    # Check 1: Files
    files_ok = check_files()
    if not files_ok:
        all_checks_passed = False
    
    # Check 2: Environment
    env_ok = check_environment()
    if not env_ok:
        all_checks_passed = False
    
    # Check 3: Dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        all_checks_passed = False
    
    # Check 4: CORS Configuration
    cors_ok = check_cors_config()
    if not cors_ok:
        all_checks_passed = False
    
    print("\n" + "=" * 40)
    
    if all_checks_passed:
        print("✅ DEPLOYMENT READY!")
        print("\n📋 Next Steps:")
        print("   1. Set VITE_FRONTEND_BASE_URL=https://feedback-catalyst.vercel.app")
        print("   2. Deploy with: gunicorn -c gunicorn.conf.py app:app")
        print("   3. Monitor logs for memory usage")
        print("\n🎉 Your app should handle CORS and memory issues properly!")
    else:
        print("❌ DEPLOYMENT NOT READY")
        print("\n🔧 Please fix the issues above before deploying")
        sys.exit(1)

if __name__ == "__main__":
    main()
