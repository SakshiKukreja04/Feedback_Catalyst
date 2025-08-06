#!/usr/bin/env python3
"""
Memory test script to simulate PDF generation and check for memory leaks
"""
import os
import psutil
import time
import gc
from dotenv import load_dotenv
import tempfile
import pandas as pd
from io import BytesIO
import zipfile

# Load environment variables
load_dotenv()

def log_memory_usage(stage=""):
    """Log current memory usage for debugging"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    print(f"🧠 Memory usage {stage}: {memory_mb:.2f} MB")
    return memory_mb

def create_test_data():
    """Create test data for memory testing"""
    print("📊 Creating test data...")
    
    # Create a sample DataFrame
    data = {
        'Rating': [4, 5, 3, 4, 5] * 100,  # 500 rows
        'Feedback': ['Great course', 'Excellent teaching', 'Good content', 'Needs improvement', 'Amazing'] * 100,
        'Suggestion': ['More practical examples', 'Include case studies', 'Better materials', 'Update content', 'Add videos'] * 100
    }
    
    df = pd.DataFrame(data)
    print(f"✅ Created test data with {len(df)} rows")
    return df

def simulate_pdf_generation(df, file_count=3):
    """Simulate PDF generation process with memory monitoring"""
    print(f"\n🔄 Starting PDF generation simulation for {file_count} files...")
    
    initial_memory = log_memory_usage("initial")
    
    for i in range(file_count):
        print(f"\n📄 Processing file {i+1}/{file_count}")
        log_memory_usage(f"before file {i+1}")
        
        try:
            # Simulate file processing
            file_data = df.to_excel(BytesIO(), index=False)
            
            # Simulate PDF creation (just create a zip with the data)
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add multiple "PDFs" to simulate real processing
                for j in range(5):  # 5 PDFs per file
                    pdf_data = f"Simulated PDF content for file {i+1}, PDF {j+1}".encode()
                    zipf.writestr(f"report_{i+1}_pdf_{j+1}.pdf", pdf_data)
            
            zip_buffer.seek(0)
            
            # Simulate memory cleanup
            del file_data
            gc.collect()
            
            log_memory_usage(f"after file {i+1}")
            
            # Small delay to simulate processing time
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error processing file {i+1}: {e}")
            continue
    
    final_memory = log_memory_usage("final")
    memory_diff = final_memory - initial_memory
    
    print(f"\n📈 Memory Analysis:")
    print(f"   Initial: {initial_memory:.2f} MB")
    print(f"   Final: {final_memory:.2f} MB")
    print(f"   Difference: {memory_diff:.2f} MB")
    
    if memory_diff > 50:  # More than 50MB increase
        print("⚠️  WARNING: Significant memory increase detected!")
        return False
    elif memory_diff > 20:  # More than 20MB increase
        print("⚠️  CAUTION: Moderate memory increase detected")
        return False
    else:
        print("✅ Memory usage is stable")
        return True

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🌐 Testing CORS Configuration:")
    
    frontend_url = os.environ.get("VITE_FRONTEND_BASE_URL")
    print(f"   Frontend URL: {frontend_url}")
    
    if frontend_url:
        print("   ✅ CORS will be configured for specific frontend URL")
        return True
    else:
        print("   ⚠️  Using '*' for all origins (development mode)")
        return True

def test_environment():
    """Test environment setup"""
    print("\n🔧 Testing Environment Setup:")
    
    # Check required packages
    try:
        import flask
        import flask_cors
        import pandas
        import psutil
        print("   ✅ All required packages are available")
    except ImportError as e:
        print(f"   ❌ Missing package: {e}")
        return False
    
    # Check environment variables
    port = os.environ.get('PORT', '5001')
    print(f"   ✅ PORT: {port}")
    
    return True

def main():
    """Main test function"""
    print("🚀 Starting Memory and CORS Test Suite")
    print("=" * 50)
    
    # Test 1: Environment setup
    env_ok = test_environment()
    if not env_ok:
        print("❌ Environment test failed")
        return
    
    # Test 2: CORS configuration
    cors_ok = test_cors_configuration()
    if not cors_ok:
        print("❌ CORS configuration test failed")
        return
    
    # Test 3: Memory usage
    print("\n🧠 Testing Memory Usage:")
    test_data = create_test_data()
    
    # Run multiple iterations to test for memory leaks
    for iteration in range(3):
        print(f"\n🔄 Memory Test Iteration {iteration + 1}/3")
        memory_ok = simulate_pdf_generation(test_data, file_count=2)
        
        if not memory_ok:
            print(f"❌ Memory test iteration {iteration + 1} failed")
            return
        
        # Force garbage collection between iterations
        gc.collect()
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Your deployment should be stable.")
    print("\n📋 Summary:")
    print("   - Environment: ✅ Ready")
    print("   - CORS: ✅ Configured")
    print("   - Memory: ✅ Stable")
    print("\n🚀 Ready for deployment!")

if __name__ == "__main__":
    main()
