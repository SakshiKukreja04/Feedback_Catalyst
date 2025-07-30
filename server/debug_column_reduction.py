import pandas as pd
import numpy as np
from feedback_processor import _get_data_and_groups, detect_likert_categories_with_gemini_subject, summarize_label

def create_test_data_with_5_columns():
    """Create test data with 5 curriculum-related columns"""
    data = {
        'Curriculum Coverage': np.random.randint(1, 6, 50),
        'Curriculum Strength': np.random.randint(1, 6, 50),
        'Curriculum Support': np.random.randint(1, 6, 50),
        'Curriculum Quality': np.random.randint(1, 6, 50),
        'Curriculum Relevance': np.random.randint(1, 6, 50),
        'Branch': ['CS', 'IT', 'ME'] * 16 + ['CS', 'IT']
    }
    return pd.DataFrame(data)

def test_column_reduction():
    """Test to identify where columns are being reduced from 5 to 3"""
    print("=== Testing Column Reduction Issue ===")
    
    # Create test data with 5 columns
    df = create_test_data_with_5_columns()
    print(f"Original DataFrame shape: {df.shape}")
    print(f"Original columns: {list(df.columns)}")
    
    # Test 1: Check _get_data_and_groups function
    print("\n--- Test 1: _get_data_and_groups function ---")
    try:
        df_test, category_groups, short_labels = _get_data_and_groups(df, 'subject')
        print(f"Category groups: {category_groups}")
        print(f"Number of category groups: {len(category_groups)}")
        print(f"Short labels: {short_labels}")
        
        # Count total columns in category groups
        total_cols = sum(len(cols) for cols in category_groups.values())
        print(f"Total columns in category groups: {total_cols}")
        
        if total_cols < 5:
            print("❌ ISSUE FOUND: Columns are being reduced!")
            print("Original columns:", list(df.columns))
            print("Columns in category groups:", [col for cols in category_groups.values() for col in cols])
        else:
            print("✅ No reduction in _get_data_and_groups")
            
    except Exception as e:
        print(f"Error in _get_data_and_groups: {e}")
    
    # Test 2: Check detect_likert_categories_with_gemini_subject function
    print("\n--- Test 2: detect_likert_categories_with_gemini_subject function ---")
    try:
        label_mapping = detect_likert_categories_with_gemini_subject(df)
        print(f"Label mapping: {label_mapping}")
        print(f"Number of mapped labels: {len(label_mapping)}")
        
        if len(label_mapping) < 5:
            print("❌ ISSUE FOUND: detect_likert_categories_with_gemini_subject is reducing columns!")
            print("Expected 5 columns, got:", len(label_mapping))
        else:
            print("✅ No reduction in detect_likert_categories_with_gemini_subject")
            
    except Exception as e:
        print(f"Error in detect_likert_categories_with_gemini_subject: {e}")
    
    # Test 3: Check summarize_label function
    print("\n--- Test 3: summarize_label function ---")
    test_columns = ['Curriculum Coverage', 'Curriculum Strength', 'Curriculum Support', 'Curriculum Quality', 'Curriculum Relevance']
    for col in test_columns:
        short_label = summarize_label(col)
        print(f"'{col}' -> '{short_label}'")
    
    # Test 4: Manual category grouping simulation
    print("\n--- Test 4: Manual category grouping simulation ---")
    label_mapping = detect_likert_categories_with_gemini_subject(df)
    category_groups = {}
    short_labels = {}
    
    for long_col, short_label in label_mapping.items():
        if long_col in df.columns:
            numeric_vals = pd.to_numeric(df[long_col], errors='coerce').dropna()
            if not numeric_vals.empty and numeric_vals.between(1, 5).all():
                category_groups.setdefault(short_label.strip(), []).append(long_col)
                short_labels[long_col] = short_label.strip()
    
    print(f"Manual category groups: {category_groups}")
    print(f"Number of manual category groups: {len(category_groups)}")
    
    # Count total columns
    total_cols = sum(len(cols) for cols in category_groups.values())
    print(f"Total columns in manual grouping: {total_cols}")
    
    if total_cols < 5:
        print("❌ ISSUE FOUND: Manual grouping also reduces columns!")
        print("This suggests the issue is in the Gemini AI processing or the column filtering logic")
    else:
        print("✅ Manual grouping preserves all columns")

if __name__ == "__main__":
    test_column_reduction() 