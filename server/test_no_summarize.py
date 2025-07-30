#!/usr/bin/env python3
"""
Test script to verify that all summarize label functions have been completely removed
"""

import pandas as pd
from feedback_processor import _get_data_and_groups, generate_summary_table, plot_ratings

# Create sample data with curriculum columns
sample_data = {
    'Curriculum Coverage': [4, 4, 3, 4, 5, 4, 3, 4, 4, 4],
    'Curriculum Strength': [4, 3, 4, 4, 4, 3, 4, 4, 4, 4],
    'Curriculum Support': [4, 4, 4, 3, 4, 4, 4, 4, 4, 4],
    'Curriculum Quality': [4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    'Curriculum Relevance': [4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    'Branch': ['CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS']
}

df = pd.DataFrame(sample_data)

print("Testing that all summarize label functions have been removed:")
print(f"DataFrame columns: {list(df.columns)}")

# Test the _get_data_and_groups function
df_result, category_groups, short_labels = _get_data_and_groups(df, 'stakeholder')

print(f"\nCategory groups: {category_groups}")
print(f"Short labels: {short_labels}")

# Verify that short_labels contains original column names
print(f"\nVerifying short_labels contain original names:")
for col, label in short_labels.items():
    print(f"  '{col}' -> '{label}'")
    if col != label:
        print(f"    ❌ ERROR: Column name was summarized!")
    else:
        print(f"    ✅ OK: Original column name preserved")

# Test generating summary table
for category, cols in category_groups.items():
    print(f"\n{'='*50}")
    print(f"Processing category: {category}")
    print(f"Columns: {cols}")
    
    summary_df = generate_summary_table(df, cols, short_labels, 'stakeholder')
    print(f"Summary table shape: {summary_df.shape}")
    if not summary_df.empty:
        categories = summary_df['Category'].tolist()
        print(f"Categories in table: {categories}")
        
        # Verify that categories in table are original column names
        for cat in categories:
            if cat in df.columns:
                print(f"  ✅ '{cat}' is original column name")
            else:
                print(f"  ❌ '{cat}' is NOT original column name")

print("\n" + "="*50)
print("Test completed! All summarize label functions should be removed.") 