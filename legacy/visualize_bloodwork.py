#!/usr/bin/env python3
"""
Blood Work Trends Visualization
Generates charts showing trends in blood work results over time
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

# Read the CSV file
df = pd.read_csv('blood_work_results.csv')

# Convert date strings to datetime
df['Date of Service'] = pd.to_datetime(df['Date of Service'])

# Sort by date
df = df.sort_values('Date of Service')

# Helper function to parse reference ranges
def parse_range(range_str):
    """Parse reference range string to get min and max values"""
    if pd.isna(range_str) or range_str == '':
        return None, None

    range_str = str(range_str).strip()

    # Handle ranges like "4.0 - 11.0"
    if '-' in range_str:
        parts = range_str.split('-')
        if len(parts) == 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except:
                pass

    # Handle ranges like "<6.0" or ">220"
    if range_str.startswith('<'):
        try:
            return None, float(range_str[1:].strip())
        except:
            pass
    elif range_str.startswith('>'):
        try:
            return float(range_str[1:].strip()), None
        except:
            pass
    elif range_str.startswith('>='):
        try:
            return float(range_str[2:].strip()), None
        except:
            pass
    elif range_str.startswith('<='):
        try:
            return None, float(range_str[2:].strip())
        except:
            pass

    return None, None

# Helper function to plot a test over time
def plot_test(ax, test_name, ylabel=None, title=None):
    """Plot a specific test result over time with reference range"""
    test_data = df[df['Test Name'] == test_name].copy()

    if len(test_data) == 0:
        ax.text(0.5, 0.5, f'No data for {test_name}',
                ha='center', va='center', transform=ax.transAxes)
        return

    # Convert results to numeric
    test_data['Result'] = pd.to_numeric(test_data['Result'], errors='coerce')
    test_data = test_data.dropna(subset=['Result'])

    if len(test_data) == 0:
        ax.text(0.5, 0.5, f'No numeric data for {test_name}',
                ha='center', va='center', transform=ax.transAxes)
        return

    # Get reference range from first entry
    ref_range = test_data['Reference Range'].iloc[0]
    min_ref, max_ref = parse_range(ref_range)

    # Plot the data
    dates = test_data['Date of Service']
    values = test_data['Result']

    # Plot line
    ax.plot(dates, values, marker='o', linewidth=2, markersize=8, label=test_name)

    # Add reference range as shaded area
    if min_ref is not None and max_ref is not None:
        ax.axhspan(min_ref, max_ref, alpha=0.2, color='green', label='Normal Range')
        ax.axhline(y=min_ref, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=max_ref, color='green', linestyle='--', alpha=0.5, linewidth=1)
    elif max_ref is not None:
        ax.axhline(y=max_ref, color='green', linestyle='--', alpha=0.7, linewidth=1, label=f'Target <{max_ref}')
    elif min_ref is not None:
        ax.axhline(y=min_ref, color='green', linestyle='--', alpha=0.7, linewidth=1, label=f'Target >{min_ref}')

    # Highlight abnormal values
    abnormal = test_data[test_data['Flag'].notna()]
    if len(abnormal) > 0:
        ax.scatter(abnormal['Date of Service'], abnormal['Result'],
                  color='red', s=150, zorder=5, marker='x', linewidths=3, label='Abnormal')

    # Add value labels on points
    for date, value in zip(dates, values):
        ax.annotate(f'{value:.1f}', (date, value),
                   textcoords="offset points", xytext=(0,10),
                   ha='center', fontsize=8, alpha=0.7)

    # Formatting
    ax.set_xlabel('Date', fontweight='bold')
    ax.set_ylabel(ylabel or test_name, fontweight='bold')
    ax.set_title(title or test_name, fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Create comprehensive visualization
fig = plt.figure(figsize=(20, 24))
fig.suptitle('Blood Work Trends - Gregory Koziol', fontsize=16, fontweight='bold', y=0.995)

# Define test categories and their plots
plots = [
    # Lipid Panel (Row 1)
    ('Cholesterol', 'Total Cholesterol (mmol/L)', 'Total Cholesterol'),
    ('HDL Cholesterol', 'HDL Cholesterol (mmol/L)', 'HDL Cholesterol'),
    ('LDL Cholesterol', 'LDL Cholesterol (mmol/L)', 'LDL Cholesterol'),
    ('Triglyceride', 'Triglyceride (mmol/L)', 'Triglycerides'),

    # Liver Function (Row 2)
    ('Alanine Aminotransferase', 'ALT (U/L)', 'ALT (Liver Enzyme)'),
    ('Gamma Glutamyl Transferase', 'GGT (U/L)', 'GGT (Liver Enzyme)'),
    ('Alkaline Phosphatase', 'ALP (U/L)', 'Alkaline Phosphatase'),
    ('Aspartate Aminotransferase', 'AST (U/L)', 'AST (Liver Enzyme)'),

    # Complete Blood Count (Row 3)
    ('WBC', 'WBC (x E9/L)', 'White Blood Cells'),
    ('RBC', 'RBC (x E12/L)', 'Red Blood Cells'),
    ('Hemoglobin', 'Hemoglobin (g/L)', 'Hemoglobin'),
    ('Platelet Count', 'Platelets (x E9/L)', 'Platelet Count'),

    # Hormones (Row 4)
    ('Testosterone', 'Testosterone (nmol/L)', 'Total Testosterone'),
    ('Testosterone Free', 'Free T (pmol/L)', 'Free Testosterone'),
    ('Thyroid Stimulating Hormone', 'TSH (mIU/L)', 'Thyroid Stimulating Hormone'),
    ('25-Hydroxy Vitamin D', 'Vitamin D (nmol/L)', 'Vitamin D (25-OH)'),

    # Metabolic Panel (Row 5)
    ('Glucose Fasting', 'Glucose (mmol/L)', 'Fasting Glucose'),
    ('Hemoglobin A1C', 'HbA1C (%)', 'Hemoglobin A1C'),
    ('Creatinine', 'Creatinine (umol/L)', 'Creatinine'),
    ('eGFR', 'eGFR (mL/min/1.73m2)', 'Kidney Function (eGFR)'),

    # Inflammation & Other (Row 6)
    ('C Reactive Protein', 'CRP (mg/L)', 'C-Reactive Protein'),
    ('Iron', 'Iron (umol/L)', 'Serum Iron'),
    ('Vitamin B12', 'B12 (pmol/L)', 'Vitamin B12'),
    ('Transferrin Saturation', 'Saturation', 'Transferrin Saturation'),
]

# Create grid of subplots
n_cols = 4
n_rows = 6

for idx, (test_name, ylabel, title) in enumerate(plots, 1):
    ax = fig.add_subplot(n_rows, n_cols, idx)
    plot_test(ax, test_name, ylabel, title)

# Adjust layout
plt.tight_layout(rect=[0, 0, 1, 0.995])

# Save the figure
output_file = 'blood_work_trends.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"✓ Visualization saved to: {output_file}")

# Also save as PDF for better quality
output_pdf = 'blood_work_trends.pdf'
plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
print(f"✓ PDF version saved to: {output_pdf}")

# Show summary statistics
print("\n" + "="*60)
print("SUMMARY - Tests with Abnormal Values")
print("="*60)

abnormal = df[df['Flag'].notna()].copy()
if len(abnormal) > 0:
    for test in abnormal['Test Name'].unique():
        test_abnormal = abnormal[abnormal['Test Name'] == test]
        print(f"\n{test}:")
        for _, row in test_abnormal.iterrows():
            flag = row['Flag']
            date = row['Date of Service'].strftime('%Y-%m-%d')
            value = row['Result']
            ref = row['Reference Range']
            print(f"  {date}: {value} ({flag}) - Normal: {ref}")

print("\n" + "="*60)
print("Visualization complete! Open the PNG or PDF file to view charts.")
print("="*60)
