#!/usr/bin/env python3
"""
Debug script for subject report generation
This script will help identify the exact issue causing PDF corruption
"""

import sys
import os
import pandas as pd
import tempfile
from io import BytesIO

# Add the server directory to the path
sys.path.append('server')

# Import the feedback processor
from feedback_processor import (
    generate_subject_report, 
    _get_data_and_groups,
    detect_likert_categories_with_gemini_subject,
    plot_ratings,
    generate_summary_table
)

def create_test_data():
    """Create a simple test dataset for debugging"""
    data = {
        'Branch': ['CS', 'CS', 'CS', 'IT', 'IT', 'IT'],
        'Subject': ['Math', 'Math', 'Math', 'Physics', 'Physics', 'Physics'],
        'Question 1 [Teaching]': [5, 4, 5, 4, 5, 4],
        'Question 2 [Teaching]': [4, 5, 4, 5, 4, 5],
        'Question 3 [Facilities]': [3, 4, 3, 4, 3, 4],
        'Question 4 [Facilities]': [4, 3, 4, 3, 4, 3],
        'Suggestions': ['Good teaching', 'More practice', 'Better labs', 'More examples', 'Good facilities', 'Need improvement']
    }
    return pd.DataFrame(data)

def test_gemini_integration():
    """Test the Gemini integration separately"""
    print("=== Testing Gemini Integration ===")
    df = create_test_data()
    
    try:
        result = detect_likert_categories_with_gemini_subject(df)
        print(f"Gemini result: {result}")
        return result
    except Exception as e:
        print(f"Gemini test failed: {e}")
        return {}

def test_data_processing():
    """Test the data processing pipeline"""
    print("\n=== Testing Data Processing ===")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        df = create_test_data()
        df.to_csv(tmp.name, index=False)
        tmp_path = tmp.name
    
    try:
        print(f"Testing with file: {tmp_path}")
        df, category_groups, short_labels = _get_data_and_groups(tmp_path, 'subject')
        
        print(f"DataFrame shape: {df.shape}")
        print(f"Category groups: {list(category_groups.keys())}")
        print(f"Short labels: {short_labels}")
        
        return df, category_groups, short_labels
        
    except Exception as e:
        print(f"Data processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_chart_generation():
    """Test chart generation separately"""
    print("\n=== Testing Chart Generation ===")
    
    df = create_test_data()
    
    # Test summary table generation
    try:
        summary_df = generate_summary_table(df, ['Question 1 [Teaching]', 'Question 2 [Teaching]'], {}, 'subject')
        print(f"Summary table shape: {summary_df.shape}")
        print(f"Summary table:\n{summary_df}")
        
        if not summary_df.empty:
            # Test chart generation
            chart_file = plot_ratings(summary_df, 'Test', 'Report', 'subject')
            print(f"Chart file generated: {chart_file}")
            return chart_file
        else:
            print("Summary table is empty, cannot generate chart")
            return None
            
    except Exception as e:
        print(f"Chart generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pdf_generation():
    """Test the complete PDF generation process"""
    print("\n=== Testing PDF Generation ===")
    
    df = create_test_data()
    
    try:
        # Process data
        df, category_groups, short_labels = _get_data_and_groups(BytesIO(df.to_csv(index=False).encode()), 'subject')
        
        if not category_groups:
            print("No category groups found, cannot generate PDF")
            return None
        
        # Generate PDF
        pdf_path = generate_subject_report(
            df, 'Test', 'All Students', 
            category_groups, short_labels, 
            'test_file', 'generalized'
        )
        
        print(f"PDF generated at: {pdf_path}")
        
        # Validate PDF
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"PDF file size: {file_size} bytes")
            if file_size > 0:
                print("✅ PDF generation successful!")
                return pdf_path
            else:
                print("❌ Generated PDF is empty")
                return None
        else:
            print("❌ PDF file was not created")
            return None
            
    except Exception as e:
        print(f"PDF generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests"""
    print("Starting debug tests for subject report generation...")
    
    # Test 1: Gemini integration
    gemini_result = test_gemini_integration()
    
    # Test 2: Data processing
    df, category_groups, short_labels = test_data_processing()
    
    # Test 3: Chart generation
    chart_file = test_chart_generation()
    
    # Test 4: Complete PDF generation
    pdf_path = test_pdf_generation()
    
    print("\n=== Summary ===")
    print(f"Gemini integration: {'✅' if gemini_result else '❌'}")
    print(f"Data processing: {'✅' if df is not None else '❌'}")
    print(f"Chart generation: {'✅' if chart_file else '❌'}")
    print(f"PDF generation: {'✅' if pdf_path else '❌'}")
    
    if pdf_path:
        print(f"\n🎉 All tests passed! PDF generated successfully at: {pdf_path}")
    else:
        print(f"\n❌ PDF generation failed. Check the debug output above for details.")

if __name__ == "__main__":
    main() 