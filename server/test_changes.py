#!/usr/bin/env python3
"""
Test script to verify the changes to feedback_processor.py
"""

import pandas as pd
import numpy as np
from feedback_processor import _get_data_and_groups, generate_summary_table

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

print("Testing with sample curriculum data:")
print(f"DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Test the _get_data_and_groups function
df_result, category_groups, short_labels = _get_data_and_groups(df, 'stakeholder')

print(f"\nCategory groups: {category_groups}")
print(f"Short labels: {short_labels}")

# Test generating summary table
for category, cols in category_groups.items():
    print(f"\nProcessing category: {category}")
    print(f"Columns: {cols}")
    
    summary_df = generate_summary_table(df, cols, short_labels, 'stakeholder')
    print(f"Summary table shape: {summary_df.shape}")
    print(f"Summary table columns: {list(summary_df.columns)}")
    print(f"Summary table:\n{summary_df}")

print("\nTest completed!") 