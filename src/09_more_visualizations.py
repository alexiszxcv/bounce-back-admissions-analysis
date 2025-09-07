import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

# Paths
CSV_DIR = Path("csv_outputs")
OUT = Path("../figures")
OUT.mkdir(exist_ok=True)

def create_patient_flow_diagram():
    """Create a CONSORT-style patient flow diagram"""
    
    # Load overlap data to get patient counts
    overlap_df = pd.read_csv(CSV_DIR / "overlap_standard.csv")
    
    total_ed_visits = overlap_df['count'].sum()
    ed_only = overlap_df[overlap_df['category'] == 'ed_only']['count'].sum()
    admit_only = overlap_df[overlap_df['category'] == 'admit_only']['count'].sum()
    both = overlap_df[overlap_df['category'] == 'both']['count'].sum()
    neither = overlap_df[overlap_df['category'] == 'neither']['count'].sum()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    color_main = '#3498db'
    color_outcome = '#e74c3c'
    color_text = '#2c3e50'
    
    # Title
    ax.text(5, 9.5, 'Patient Flow Diagram: ED Visits and Outcomes', 
            ha='center', va='center', fontsize=16, fontweight='bold', color=color_text)
    
    # Main cohort box
    ax.add_patch(plt.Rectangle((3.5, 7.5), 3, 1, facecolor=color_main, alpha=0.3, edgecolor=color_main, linewidth=2))
    ax.text(5, 8, f'Total ED Visits\nn = {total_ed_visits:,}', 
            ha='center', va='center', fontsize=12, fontweight='bold', color=color_text)
    
    # Arrows down
    ax.annotate('', xy=(5, 7.2), xytext=(5, 7.5), arrowprops=dict(arrowstyle='->', lw=2, color=color_text))
    
    # Outcome boxes
    box_width = 1.8
    box_height = 0.8
    y_pos = 6
    
    # Neither
    ax.add_patch(plt.Rectangle((0.5, y_pos), box_width, box_height, facecolor='lightgray', alpha=0.5, edgecolor='gray', linewidth=1))
    ax.text(0.5 + box_width/2, y_pos + box_height/2, f'No Revisit\nor Bounce Back Admission\nn = {neither:,}\n({neither/total_ed_visits*100:.1f}%)', 
            ha='center', va='center', fontsize=10, color=color_text)
    
    # ED only
    ax.add_patch(plt.Rectangle((2.5, y_pos), box_width, box_height, facecolor=color_outcome, alpha=0.3, edgecolor=color_outcome, linewidth=2))
    ax.text(2.5 + box_width/2, y_pos + box_height/2, f'ED Revisit\nOnly\nn = {ed_only:,}\n({ed_only/total_ed_visits*100:.1f}%)', 
            ha='center', va='center', fontsize=10, fontweight='bold', color=color_text)
    
    # Admit only
    ax.add_patch(plt.Rectangle((4.5, y_pos), box_width, box_height, facecolor='#f39c12', alpha=0.3, edgecolor='#f39c12', linewidth=2))
    ax.text(4.5 + box_width/2, y_pos + box_height/2, f'Bounce Back Admission\nOnly\nn = {admit_only:,}\n({admit_only/total_ed_visits*100:.1f}%)', 
            ha='center', va='center', fontsize=10, fontweight='bold', color=color_text)
    
    # Both
    ax.add_patch(plt.Rectangle((6.5, y_pos), box_width, box_height, facecolor='#9b59b6', alpha=0.3, edgecolor='#9b59b6', linewidth=2))
    ax.text(6.5 + box_width/2, y_pos + box_height/2, f'Both ED Revisit\nand Bounce Back Admission\nn = {both:,}\n({both/total_ed_visits*100:.1f}%)', 
            ha='center', va='center', fontsize=10, fontweight='bold', color=color_text)
    
    # Arrows from main box to outcome boxes
    for x_pos in [1.4, 3.4, 5.4, 7.4]:
        ax.annotate('', xy=(x_pos, y_pos + box_height + 0.1), xytext=(5, 7.2), 
                   arrowprops=dict(arrowstyle='->', lw=1.5, color=color_text, alpha=0.7))
    
    # Add key findings
    ax.text(5, 4.5, 'Key Findings:', ha='center', va='top', fontsize=14, fontweight='bold', color=color_text)
    
    ed_rate = (ed_only + both) / total_ed_visits * 100
    readmit_rate = (admit_only + both) / total_ed_visits * 100
    overlap_rate = both / total_ed_visits * 100
    
    findings_text = f"""
    • Overall ED Revisit Rate: {ed_rate:.1f}%
    • Overall Bounce Back Admission Rate: {readmit_rate:.1f}%
    • Overlap Rate (Both Outcomes): {overlap_rate:.1f}%
    • Patients with Any Adverse Outcome: {(ed_only + admit_only + both)/total_ed_visits*100:.1f}%
    """
    
    ax.text(5, 4, findings_text, ha='center', va='top', fontsize=11, color=color_text,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray'))
    
    plt.tight_layout()
    plt.savefig(OUT / "patient_flow_diagram.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_correlation_matrix():
    """Create a correlation matrix of key variables"""
    
    # Load all available data
    df_ed_race = pd.read_csv(CSV_DIR / "ed_bounceback_by_race.csv", index_col=0)
    df_readmit_race = pd.read_csv(CSV_DIR / "readmit_by_race.csv", index_col=0)
    df_ed_dx = pd.read_csv(CSV_DIR / "ed_bounceback_by_diagnosis.csv", index_col=0)
    df_readmit_dx = pd.read_csv(CSV_DIR / "readmit_by_diagnosis.csv", index_col=0)
    
    # Create correlation data
    correlation_data = []
    
    # Get common races and diagnoses
    common_races = set(df_ed_race.index).intersection(set(df_readmit_race.index))
    common_dx = set(df_ed_dx.index).intersection(set(df_readmit_dx.index))
    
    for race in common_races:
        if pd.notna(df_ed_race.loc[race, 'rate']) and pd.notna(df_readmit_race.loc[race, 'rate']):
            correlation_data.append({
                'group': race,
                'type': 'Race',
                'ed_rate': df_ed_race.loc[race, 'rate'] * 100,
                'readmit_rate': df_readmit_race.loc[race, 'rate'] * 100
            })
    
    for dx in list(common_dx)[:15]:  # Top 15 diagnoses
        if pd.notna(df_ed_dx.loc[dx, 'rate']) and pd.notna(df_readmit_dx.loc[dx, 'rate']):
            correlation_data.append({
                'group': dx[:30] + '...' if len(dx) > 30 else dx,  # Truncate long names
                'type': 'Diagnosis',
                'ed_rate': df_ed_dx.loc[dx, 'rate'] * 100,
                'readmit_rate': df_readmit_dx.loc[dx, 'rate'] * 100
            })
    
    df_corr = pd.DataFrame(correlation_data)
    
    # Create scatter plot with correlation
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Color by type
    race_data = df_corr[df_corr['type'] == 'Race']
    dx_data = df_corr[df_corr['type'] == 'Diagnosis']
    
    if len(race_data) > 0:
        ax.scatter(race_data['ed_rate'], race_data['readmit_rate'], 
                  s=100, alpha=0.7, color='#e74c3c', label='Race/Ethnicity', marker='o')
    
    if len(dx_data) > 0:
        ax.scatter(dx_data['ed_rate'], dx_data['readmit_rate'], 
                  s=80, alpha=0.7, color='#3498db', label='Diagnosis', marker='s')
    
    # Calculate and plot correlation line
    if len(df_corr) > 1:
        correlation = np.corrcoef(df_corr['ed_rate'], df_corr['readmit_rate'])[0, 1]
        z = np.polyfit(df_corr['ed_rate'], df_corr['readmit_rate'], 1)
        p = np.poly1d(z)
        ax.plot(df_corr['ed_rate'], p(df_corr['ed_rate']), "r--", alpha=0.8, linewidth=2)
        
        # Add correlation text
        ax.text(0.05, 0.95, f'Pearson r = {correlation:.3f}', 
                transform=ax.transAxes, va='top', ha='left', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('ED Revisit Rate (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Bounce Back Admission Rate (%)', fontsize=14, fontweight='bold')
    ax.set_title('Correlation Between ED Revisit and Bounce Back Admission Rates', 
                fontsize=16, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    
    # Add diagonal reference line
    max_val = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=1)
    ax.text(max_val*0.8, max_val*0.9, 'Equal rates', rotation=45, alpha=0.5, fontsize=10)
    
    plt.tight_layout()
    plt.savefig(OUT / "correlation_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_statistical_summary_table():
    """Create a publication-ready summary statistics table"""
    
    # Load overlap data
    overlap_df = pd.read_csv(CSV_DIR / "overlap_standard.csv")
    total_visits = overlap_df['count'].sum()
    
    # Load race data
    df_ed_race = pd.read_csv(CSV_DIR / "ed_bounceback_by_race.csv", index_col=0)
    df_readmit_race = pd.read_csv(CSV_DIR / "readmit_by_race.csv", index_col=0)
    
    # Calculate summary statistics
    summary_stats = {
        'Total ED Visits': f"{total_visits:,}",
        'ED Revisit Rate': f"{(overlap_df[overlap_df['category'].isin(['ed_only', 'both'])]['count'].sum() / total_visits * 100):.1f}%",
        'Bounce Back Admission Rate': f"{(overlap_df[overlap_df['category'].isin(['admit_only', 'both'])]['count'].sum() / total_visits * 100):.1f}%",
        'Overlap Rate': f"{(overlap_df[overlap_df['category'] == 'both']['count'].sum() / total_visits * 100):.1f}%",
        'Mean ED Revisit Rate by Race': f"{df_ed_race['rate'].mean() * 100:.1f}% ± {df_ed_race['rate'].std() * 100:.1f}%",
        'Mean Bounce Back Rate by Race': f"{df_readmit_race['rate'].mean() * 100:.1f}% ± {df_readmit_race['rate'].std() * 100:.1f}%"
    }
    
    # Create table visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table data
    table_data = [[key, value] for key, value in summary_stats.items()]
    
    table = ax.table(cellText=table_data,
                    colLabels=['Metric', 'Value'],
                    cellLoc='left',
                    loc='center',
                    colWidths=[0.7, 0.3])
    
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.5)
    
    # Style the table
    for i in range(len(table_data) + 1):
        for j in range(2):
            cell = table[(i, j)]
            if i == 0:  # Header
                cell.set_facecolor('#3498db')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#f8f9fa' if i % 2 == 0 else 'white')
                cell.set_text_props(weight='bold' if j == 0 else 'normal')
    
    ax.set_title('Summary Statistics: ED Revisit and Bounce Back Admission Analysis', 
                fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(OUT / "summary_statistics_table.png", dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Generate all visualizations"""
    print("Creating visualizations...")
    
    try:
        create_patient_flow_diagram()
        print("✓ Patient flow diagram created")
        
        create_correlation_matrix()
        print("✓ Correlation analysis created")
        
        create_statistical_summary_table()
        print("✓ Summary statistics table created")
        
        print(f"\nAll visualizations saved to: {OUT.absolute()}")
        
        # List all generated files
        plot_files = list(OUT.glob("*.png"))
        if plot_files:
            print("\nGenerated plots:")
            plots = [
                "patient_flow_diagram.png",
                "correlation_analysis.png",
                "summary_statistics_table.png"
            ]
            for plot in plots:
                if (OUT / plot).exists():
                    print(f"  - {plot}")
        
    except Exception as e:
        print(f"Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
