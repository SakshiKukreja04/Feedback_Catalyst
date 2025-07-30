#!/usr/bin/env python3
"""
Test script to run stakeholder report generation and see what's happening
"""

import pandas as pd
from feedback_processor import _get_data_and_groups, generate_stakeholder_report

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

print("Testing stakeholder report generation:")
print(f"DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Get data and groups
df_result, category_groups, short_labels = _get_data_and_groups(df, 'stakeholder')

print(f"\nCategory groups: {category_groups}")
print(f"Short labels: {short_labels}")

# Test generating stakeholder report
try:
    pdf_path = generate_stakeholder_report(df, 'Overall', 'All Students', category_groups, short_labels, 'test_file.xlsx', 'generalized')
    print(f"\nPDF generated at: {pdf_path}")
except Exception as e:
    print(f"Error generating report: {e}")

print("\nTest completed!") 