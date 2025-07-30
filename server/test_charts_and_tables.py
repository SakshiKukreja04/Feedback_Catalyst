#!/usr/bin/env python3
"""
Test script to verify that both charts and tables use original column names
"""

import pandas as pd
import numpy as np
from feedback_processor import _get_data_and_groups, generate_summary_table, plot_ratings

# Create sample data similar to curriculum feedback
sample_data = {
    'Curriculum Coverage': [4, 4, 3, 4, 5, 4, 3, 4, 4, 4],
    'Curriculum Strength': [4, 3, 4, 4, 4, 3, 4, 4, 4, 4],
    'Curriculum Support': [4, 4, 4, 3, 4, 4, 4, 4, 4, 4],
    'Curriculum Quality': [4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    'Curriculum Relevance': [4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    'Branch': ['CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS', 'CS']
}

df = pd.DataFrame(sample_data)

print("Testing charts and tables with original column names:")
print(f"DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Test the _get_data_and_groups function
df_result, category_groups, short_labels = _get_data_and_groups(df, 'stakeholder')

print(f"\nCategory groups: {category_groups}")
print(f"Short labels: {short_labels}")

# Test generating summary table and chart for each category
for category, cols in category_groups.items():
    print(f"\n{'='*50}")
    print(f"Processing category: {category}")
    print(f"Columns: {cols}")
    
    # Generate summary table
    summary_df = generate_summary_table(df, cols, short_labels, 'stakeholder')
    print(f"Summary table shape: {summary_df.shape}")
    print(f"Summary table columns: {list(summary_df.columns)}")
    print(f"Summary table:\n{summary_df}")
    
    # Check that the Category column contains original column names
    if not summary_df.empty:
        categories = summary_df['Category'].tolist()
        print(f"Categories in table: {categories}")
        
        # Test chart generation
        try:
            chart_file = plot_ratings(summary_df, category, "Test Report", 'stakeholder')
            print(f"Chart generated: {chart_file}")
        except Exception as e:
            print(f"Chart generation failed: {e}")

print("\n" + "="*50)
print("Test completed! Both tables and charts should now use original column names.") 