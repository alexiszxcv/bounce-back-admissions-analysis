# src/07_generate_report.py

from pathlib import Path
import pandas as pd

def generate_report():
    """Generate a text report summarizing the bounce-back analysis results"""
    
    FIGURES = Path("figures")
    CSV_DIR = Path("csv_outputs")
    
    print("=" * 80)
    print("ED REVISIT AND BOUNCE BACK ADMISSION ANALYSIS REPORT")
    print("=" * 80)
    
    # Read overlap data for main results
    if (CSV_DIR / "overlap_standard.csv").exists():
        df_overlap = pd.read_csv(CSV_DIR / "overlap_standard.csv")
        total = df_overlap['count'].sum()
        
        print(f"\nOVERALL RESULTS (n={total:,} ED discharges)")
        print("-" * 50)
        
        for _, row in df_overlap.iterrows():
            category = row['category'].replace('_', ' ').title()
            count = int(row['count'])
            rate = row['rate'] * 100
            print(f"{category:20s}: {count:6,} ({rate:5.1f}%)")
        
        # Calculate derived metrics
        ed_revisit = df_overlap[df_overlap['category'].isin(['both', 'ed_only'])]['count'].sum()
        readmit = df_overlap[df_overlap['category'].isin(['both', 'admit_only'])]['count'].sum()
        
        print(f"\nKEY METRICS")
        print("-" * 50)
        print(f"Total ED Revisit Rate       : {ed_revisit/total*100:5.1f}%")
        print(f"Total Hospital Readmit Rate : {readmit/total*100:5.1f}%")
        print(f"Overlap Rate                : {df_overlap[df_overlap['category']=='both']['rate'].iloc[0]*100:5.1f}%")
    
    # Monthly trends summary
    if (CSV_DIR / "ed_bounceback_monthly.csv").exists():
        df_monthly = pd.read_csv(CSV_DIR / "ed_bounceback_monthly.csv")
        avg_rate = df_monthly['rate'].mean() * 100
        max_rate = df_monthly['rate'].max() * 100
        min_rate = df_monthly['rate'].min() * 100
        
        print(f"\nMONTHLY TRENDS - ED REVISIT")
        print("-" * 50)
        print(f"Average Monthly Rate : {avg_rate:5.1f}%")
        print(f"Highest Monthly Rate : {max_rate:5.1f}%")
        print(f"Lowest Monthly Rate  : {min_rate:5.1f}%")
    
    if (CSV_DIR / "readmit_monthly.csv").exists():
        df_monthly = pd.read_csv(CSV_DIR / "readmit_monthly.csv")
        avg_rate = df_monthly['rate'].mean() * 100
        max_rate = df_monthly['rate'].max() * 100
        min_rate = df_monthly['rate'].min() * 100
        
        print(f"\nMONTHLY TRENDS - BOUNCE BACK")
        print("-" * 50)
        print(f"Average Monthly Rate : {avg_rate:5.1f}%")
        print(f"Highest Monthly Rate : {max_rate:5.1f}%")
        print(f"Lowest Monthly Rate  : {min_rate:5.1f}%")
    
    # Demographic breakdown highlights
    demo_files = [
        ("ed_bounceback_by_race.csv", "ED Revisit by Race"),
        ("readmit_by_race.csv", "Bounce Back Admission by Race"),
    ]
    
    for filename, title in demo_files:
        filepath = CSV_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0)
            max_group = df['rate'].idxmax()
            max_rate = df['rate'].max() * 100
            min_group = df['rate'].idxmin()
            min_rate = df['rate'].min() * 100
            
            print(f"\n🏥 {title.upper()}")
            print("-" * 50)
            print(f"Highest: {max_group:15s} {max_rate:5.1f}%")
            print(f"Lowest:  {min_group:15s} {min_rate:5.1f}%")
    
    # Top diagnosis breakdown with meaningful sample sizes
    if (CSV_DIR / "ed_bounceback_by_diagnosis.csv").exists():
        df = pd.read_csv(CSV_DIR / "ed_bounceback_by_diagnosis.csv", index_col=0)
        # Filter for meaningful sample sizes (same as visualization)
        df_filtered = df[(df['d'] >= 10) & (df['n'] >= 2)]
        
        if len(df_filtered) > 0:
            top_5 = df_filtered.sort_values('rate', ascending=False).head(5)
            
            # Try to load diagnosis descriptions
            try:
                diag_df = pd.read_csv("data/diagnosis.csv")
                diag_map = diag_df.drop_duplicates('icd_code').set_index('icd_code')['icd_title'].to_dict()
            except:
                diag_map = {}
            
            print(f"\n🩺 TOP 5 DIAGNOSES - ED REVISIT (≥10 cases, ≥2 events)")
            print("-" * 50)
            for i, (diag, row) in enumerate(top_5.iterrows(), 1):
                desc = diag_map.get(diag, diag)[:40]  # Truncate long descriptions
                print(f"{i}. {desc:40s} {row['rate']*100:5.1f}% (n={int(row['n'])}/{int(row['d'])})")
        else:
            print(f"\n🩺 No diagnoses found with adequate sample size for ED REVISIT")
    
    if (CSV_DIR / "readmit_by_diagnosis.csv").exists():
        df = pd.read_csv(CSV_DIR / "readmit_by_diagnosis.csv", index_col=0)
        # Filter for meaningful sample sizes (same as visualization)
        df_filtered = df[(df['d'] >= 10) & (df['n'] >= 2)]
        
        if len(df_filtered) > 0:
            top_5 = df_filtered.sort_values('rate', ascending=False).head(5)
            
            # Try to load diagnosis descriptions
            try:
                diag_df = pd.read_csv("data/diagnosis.csv")
                diag_map = diag_df.drop_duplicates('icd_code').set_index('icd_code')['icd_title'].to_dict()
            except:
                diag_map = {}
            
            print(f"\n🩺 TOP 5 DIAGNOSES - Bounce back (≥10 cases, ≥2 events)")
            print("-" * 50)
            for i, (diag, row) in enumerate(top_5.iterrows(), 1):
                desc = diag_map.get(diag, diag)[:40]  # Truncate long descriptions  
                print(f"{i}. {desc:40s} {row['rate']*100:5.1f}% (n={int(row['n'])}/{int(row['d'])})")
        else:
            print(f"\n🩺 No diagnoses found with adequate sample size for readmissions")
    
    # Generated files summary
    plot_files = list(FIGURES.glob("*.png"))
    csv_files = list(CSV_DIR.glob("*.csv"))
    
    print(f"\nGENERATED FILES")
    print("-" * 50)
    print(f"CSV Data Files: {len(csv_files)}")
    print(f"Visualization Files: {len(plot_files)}")
    
    print(f"\nKEY VISUALIZATIONS CREATED:")
    key_plots = [
        "bounce_back_dashboard.png",
        "overlap_standard_visualization.png", 
        "monthly_trends.png",
        "ed_bounceback_by_diagnosis_plot.png",
        "readmit_by_diagnosis_plot.png"
    ]
    
    for plot in key_plots:
        if (FIGURES / plot).exists():
            print(f"  ✓ {plot}")
        else:
            print(f"  ✗ {plot} (not found)")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 50)
    print("  • Review the dashboard (bounce_back_dashboard.png) for overall patterns")
    print("  • Examine monthly trends for seasonal variations")
    print("  • Focus on high-risk diagnoses for targeted interventions")
    print("  • Consider demographic disparities in bounce-back rates")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    generate_report()
