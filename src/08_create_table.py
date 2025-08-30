# src/08_create_table.py
"""Generate tables"""

import pandas as pd
import numpy as np
from pathlib import Path

CSV_DIR = Path("csv_outputs")
OUT = Path("figures")

def create_table_1():
    """Create Table 1: Patient characteristics and outcomes"""
    
    # Load overlap data for overall statistics
    overlap_file = CSV_DIR / "overlap_standard.csv"
    if not overlap_file.exists():
        print("Missing overlap data file")
        return
    
    df_overlap = pd.read_csv(overlap_file)
    total_visits = df_overlap['count'].sum()
    
    # Calculate rates
    ed_revisit_rate = (df_overlap[df_overlap['category'].isin(['both', 'ed_only'])]['count'].sum() / total_visits) * 100
    readmit_rate = (df_overlap[df_overlap['category'].isin(['both', 'admit_only'])]['count'].sum() / total_visits) * 100
    both_rate = (df_overlap[df_overlap['category'] == 'both']['count'].sum() / total_visits) * 100
    
    # Load demographic breakdowns
    results = []
    
    # Overall statistics
    results.append({
        'Characteristic': 'Overall',
        'Category': 'Total ED Visits',
        'N': f'{total_visits:,}',
        'ED Revisit Rate (%)': f'{ed_revisit_rate:.1f}',
        'Bounce Back Admission Rate (%)': f'{readmit_rate:.1f}',
        'Both Events Rate (%)': f'{both_rate:.1f}'
    })
    
    # Add demographic breakdowns
    demo_files = [
        ('ed_bounceback_by_age.csv', 'readmit_by_age.csv', 'Age Group'),
        ('ed_bounceback_by_sex.csv', 'readmit_by_sex.csv', 'Sex'),
        ('ed_bounceback_by_race.csv', 'readmit_by_race.csv', 'Race/Ethnicity')
    ]
    
    for ed_file, readmit_file, category in demo_files:
        ed_path = CSV_DIR / ed_file
        readmit_path = CSV_DIR / readmit_file
        
        if ed_path.exists() and readmit_path.exists():
            df_ed = pd.read_csv(ed_path, index_col=0)
            df_readmit = pd.read_csv(readmit_path, index_col=0)
            
            for idx in df_ed.index:
                if idx in df_readmit.index:
                    ed_rate = df_ed.loc[idx, 'rate'] * 100
                    readmit_rate = df_readmit.loc[idx, 'rate'] * 100
                    n_total = int(df_ed.loc[idx, 'd'])
                    
                    results.append({
                        'Characteristic': category,
                        'Category': str(idx),
                        'N': f'{n_total:,}',
                        'ED Revisit Rate (%)': f'{ed_rate:.1f}',
                        'Bounce Back Admission Rate (%)': f'{readmit_rate:.1f}',
                    })
    
    # Create DataFrame and save
    table1_df = pd.DataFrame(results)
    table1_df.to_csv(OUT / "table1_patient_characteristics.csv", index=False)
    
    # Create formatted version for publication
    with open(OUT / "table1_formatted.txt", 'w') as f:
        f.write("Table 1. Patient Characteristics and Outcome Rates\n")
        f.write("=" * 60 + "\n\n")
        
        current_char = ""
        for _, row in table1_df.iterrows():
            if row['Characteristic'] != current_char:
                if current_char != "":
                    f.write("\n")
                f.write(f"{row['Characteristic']}\n")
                current_char = row['Characteristic']
            
            f.write(f"  {row['Category']:<25} {row['N']:>8} {row['ED Revisit Rate (%)']:>8} {row['Bounce Back Admission Rate (%)']:>8}\n")
    
    print("✓ Table 1 created: Patient characteristics and outcomes")

def create_table_2():
    """Create Table 2: Top diagnoses associated with bounce-back"""
    
    # Load diagnosis data
    ed_diag_file = CSV_DIR / "ed_bounceback_by_diagnosis.csv"
    readmit_diag_file = CSV_DIR / "readmit_by_diagnosis.csv"
    
    if not (ed_diag_file.exists() and readmit_diag_file.exists()):
        print("Missing diagnosis data files")
        return
    
    df_ed = pd.read_csv(ed_diag_file, index_col=0)
    df_readmit = pd.read_csv(readmit_diag_file, index_col=0)
    
    # Filter for meaningful sample sizes
    df_ed_filtered = df_ed[(df_ed['d'] >= 10) & (df_ed['n'] >= 2)].copy()
    df_readmit_filtered = df_readmit[(df_readmit['d'] >= 10) & (df_readmit['n'] >= 2)].copy()
    
    # Get top 10 for each
    top_ed = df_ed_filtered.sort_values('rate', ascending=False).head(10)
    top_readmit = df_readmit_filtered.sort_values('rate', ascending=False).head(10)
    
    # Try to load diagnosis descriptions
    diagnosis_map = {}
    try:
        diag_df = pd.read_csv("data/diagnosis.csv")
        diagnosis_map = diag_df.drop_duplicates('icd_code').set_index('icd_code')['icd_title'].to_dict()
    except:
        pass
    
    # Create combined table
    results = []
    
    # ED bounce-back section
    results.append(['SECTION', 'ED Revisit (Top 10)', '', '', '', ''])
    for idx, row in top_ed.iterrows():
        description = diagnosis_map.get(idx, idx)[:50] + "..." if len(diagnosis_map.get(idx, idx)) > 50 else diagnosis_map.get(idx, idx)
        results.append([
            'ED',
            idx,
            description,
            int(row['n']),
            int(row['d']),
            f"{row['rate']*100:.1f}"
        ])
    
    # Readmission section
    results.append(['SECTION', 'Bounce Back Admission (Top 10)', '', '', '', ''])
    for idx, row in top_readmit.iterrows():
        description = diagnosis_map.get(idx, idx)[:50] + "..." if len(diagnosis_map.get(idx, idx)) > 50 else diagnosis_map.get(idx, idx)
        results.append([
            'Readmit',
            idx,
            description,
            int(row['n']),
            int(row['d']),
            f"{row['rate']*100:.1f}"
        ])
    
    # Create DataFrame
    table2_df = pd.DataFrame(results, columns=[
        'Outcome_Type', 'ICD_Code', 'Description', 'Events', 'Total', 'Rate_Percent'
    ])
    
    table2_df.to_csv(OUT / "table2_top_diagnoses.csv", index=False)
    
    # Create formatted version
    with open(OUT / "table2_formatted.txt", 'w') as f:
        f.write("Table 2. Top Diagnoses Associated with Bounce-back Events\n")
        f.write("=" * 80 + "\n\n")
        
        for _, row in table2_df.iterrows():
            if row['Outcome_Type'] == 'SECTION':
                f.write(f"\n{row['ICD_Code']}\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'ICD Code':<12} {'Description':<35} {'Events':>8} {'Total':>8} {'Rate%':>8}\n")
                f.write("-" * 80 + "\n")
            else:
                f.write(f"{row['ICD_Code']:<12} {row['Description']:<35} {row['Events']:>8} {row['Total']:>8} {row['Rate_Percent']:>8}\n")
    
    print("✓ Table 2 created: Top diagnoses for bounce-back events")

def create_methods_summary():
    """Create methods summary for paper"""
    
    with open(OUT / "methods_summary.txt", 'w') as f:
        f.write("METHODS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Study Design: Retrospective cohort study\n\n")
        
        f.write("Setting: Emergency department visits from MIMIC-IV database\n\n")
        
        f.write("Participants: Adult patients (≥18 years) discharged from the emergency department\n\n")
        
        f.write("Exposures: Patient demographics (age, sex, race/ethnicity), primary diagnosis\n\n")
        
        f.write("Outcomes:\n")
        f.write("- Primary: ED revisit within 72 hours of discharge\n")
        f.write("- Secondary: Hospital bounce back admission within 72 hours of ED discharge\n")
        f.write("- Tertiary: Combined outcome (either revisit or bounce back admission)\n\n")
        
        f.write("Statistical Analysis:\n")
        f.write("- Descriptive statistics for patient characteristics\n")
        f.write("- Time-to-event analysis with cumulative incidence curves\n")
        f.write("- Multivariable logistic regression for risk factors\n")
        f.write("- Seasonal pattern analysis using heatmaps\n")
        f.write("- Subgroup analyses by demographics and diagnosis\n\n")
        
        f.write("Data Processing:\n")
        f.write("- Race categories standardized to 8 major groups\n")
        f.write("- Age groups: 18-34, 35-49, 50-64, 65-79, 80+ years\n")
        f.write("- Diagnosis analysis limited to conditions with ≥10 cases and ≥2 events\n")
        f.write("- Time trends analyzed monthly over study period\n\n")
    
    print("✓ Methods summary created")

def main():
    """Generatetables and summaries"""
    print("Creating tables and summaries...")
    
    OUT.mkdir(exist_ok=True)
    
    create_table_1()
    create_table_2() 
    create_methods_summary()
    
    print(f"\nAll tables saved to: {OUT.absolute()}")
    print("\nGenerated files:")
    print("  - table1_patient_characteristics.csv")
    print("  - table1_formatted.txt")
    print("  - table2_top_diagnoses.csv") 
    print("  - table2_formatted.txt")
    print("  - methods_summary.txt")

if __name__ == "__main__":
    main()
