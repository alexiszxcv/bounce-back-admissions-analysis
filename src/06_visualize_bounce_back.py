# src/06_visualize_bounce_back.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
from pathlib import Path
import os

# Set style
plt.style.use('default')
sns.set_palette("husl")

# Paths
FIGURES = Path("figures")
CSV_DIR = Path("csv_outputs")
OUT = FIGURES  # Save plots in figures directory

def create_figure_with_subtitle(title, subtitle="", figsize=(10, 6)):
    """Create a figure with title and subtitle"""
    fig, ax = plt.subplots(figsize=figsize)
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    if subtitle:
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha='center', 
                fontsize=10, style='italic')
    return fig, ax

def load_and_plot_overlap():
    """Plot overlap between ED revisit and bounce back"""
    # Standard overlap
    if (CSV_DIR / "overlap_standard.csv").exists():
        df_std = pd.read_csv(CSV_DIR / "overlap_standard.csv")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Pie chart
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        wedges, texts, autotexts = ax1.pie(df_std['count'], labels=df_std['category'], 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Standard Overlap: ED Revisit vs Bounce Back')
        
        # Bar chart with rates
        bars = ax2.bar(df_std['category'], df_std['rate']*100, color=colors)
        ax2.set_title('Rates by Category')
        ax2.set_ylabel('Percentage (%)')
        ax2.set_xlabel('Category')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, rate in zip(bars, df_std['rate']*100):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{rate:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(OUT / "overlap_standard_visualization.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    # Strict overlap (if exists)
    if (CSV_DIR / "overlap_strict_revisit_then_admit.csv").exists():
        df_strict = pd.read_csv(CSV_DIR / "overlap_strict_revisit_then_admit.csv")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24']
        wedges, texts, autotexts = ax1.pie(df_strict['count'], labels=df_strict['category'], 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Strict Overlap: Revisit → Then Admit')
        
        bars = ax2.bar(df_strict['category'], df_strict['rate']*100, color=colors)
        ax2.set_title('Rates by Category (Strict Definition)')
        ax2.set_ylabel('Percentage (%)')
        ax2.set_xlabel('Category')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        for bar, rate in zip(bars, df_strict['rate']*100):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{rate:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(OUT / "overlap_strict_visualization.png", dpi=300, bbox_inches='tight')
        plt.close()

def plot_time_trends():
    """Plot monthly trends for ED revisits and bounce back admissions"""
    ed_monthly = CSV_DIR / "ed_bounceback_monthly.csv"
    readmit_monthly = CSV_DIR / "readmit_monthly.csv"
    
    if ed_monthly.exists() and readmit_monthly.exists():
        df_ed = pd.read_csv(ed_monthly)
        df_readmit = pd.read_csv(readmit_monthly)
        
        # Convert the month column to proper datetime
        # Handle the MIMIC-IV shifted dates by mapping to normal years for visualization
        df_ed['month_date'] = pd.to_datetime(df_ed['month'])
        df_readmit['month_date'] = pd.to_datetime(df_readmit['month'])
        
        # Shift years to normal range for better visualization (2110 -> 2021, etc.)
        df_ed['month_date'] = df_ed['month_date'] - pd.DateOffset(years=89)  # 2110 -> 2021
        df_readmit['month_date'] = df_readmit['month_date'] - pd.DateOffset(years=89)
        
    # Sort by date to ensure proper chronological order
    df_ed = df_ed.sort_values('month_date')
    df_readmit = df_readmit.sort_values('month_date')
    # Filter for 2016-2025
    start = pd.Timestamp('2016-01-01')
    end = pd.Timestamp('2025-12-31')
    df_ed = df_ed[(df_ed['month_date'] >= start) & (df_ed['month_date'] <= end)]
    df_readmit = df_readmit[(df_readmit['month_date'] >= start) & (df_readmit['month_date'] <= end)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # ED revisit trend
    ax1.plot(df_ed['month_date'], df_ed['rate']*100, marker='o', linewidth=2, 
         markersize=4, color='#e74c3c', label='ED Revisit Rate')
    ax1.set_title('Monthly ED Revisit Rate Trend', fontweight='bold', fontsize=14)
    ax1.set_ylabel('Revisit Rate (%)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Bounce back trend
    ax2.plot(df_readmit['month_date'], df_readmit['rate']*100, marker='s', linewidth=2, 
         markersize=4, color='#3498db', label='Bounce Back Admission Rate')
    ax2.set_title('Monthly Bounce Back Admission Rate Trend', fontweight='bold', fontsize=14)
    ax2.set_ylabel('Bounce Back Admission Rate (%)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Format x-axis for both plots
    from matplotlib.dates import DateFormatter, YearLocator, MonthLocator

    # Set major ticks to show every few months for readability
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_locator(MonthLocator(interval=6))  # Every 6 months
        ax.xaxis.set_minor_locator(MonthLocator(interval=3))  # Every 3 months
        ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))  # e.g., "Jan 2021"
        # Rotate labels and improve spacing
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        # Set reasonable y-axis limits
        y_max = max(ax.get_ylim()[1], 15)  # At least 15% for scale
        ax.set_ylim(0, y_max)

    # Add summary statistics as text
    ed_avg = df_ed['rate'].mean() * 100
    ed_trend = "increasing" if df_ed['rate'].iloc[-12:].mean() > df_ed['rate'].iloc[:12].mean() else "decreasing"

    readmit_avg = df_readmit['rate'].mean() * 100
    readmit_trend = "increasing" if df_readmit['rate'].iloc[-12:].mean() > df_readmit['rate'].iloc[:12].mean() else "decreasing"

    # Add text boxes with summary info
    ax1.text(0.02, 0.98, f'Avg: {ed_avg:.1f}%\nTrend: {ed_trend}', 
        transform=ax1.transAxes, va='top', ha='left', fontsize=10,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    ax2.text(0.02, 0.98, f'Avg: {readmit_avg:.1f}%\nTrend: {readmit_trend}', 
        transform=ax2.transAxes, va='top', ha='left', fontsize=10,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUT / "monthly_trends.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_demographic_comparisons():
    """Plot demographic breakdowns for revisit and bounce back rates"""
    
    # Age groups
    age_files = [
        ("ed_bounceback_by_age.csv", "ED Revisit by Age Group", '#e74c3c'),
        ("readmit_by_age.csv", "Bounce Back Admission by Age Group", '#3498db')
    ]
    
    for filename, title, color in age_files:
        filepath = CSV_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(df.index, df['rate']*100, color=color, alpha=0.7)
            ax.set_title(title, fontweight='bold')
            ax.set_ylabel('Rate (%)')
            ax.set_xlabel('Age Group')
            
            # Add value labels
            for bar, rate in zip(bars, df['rate']*100):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{rate:.1f}%', ha='center', va='bottom')
            
            # Add sample size annotations
            for i, (idx, row) in enumerate(df.iterrows()):
                ax.text(i, -max(df['rate']*100)*0.05, f'n={int(row["d"])}', 
                       ha='center', va='top', fontsize=8, alpha=0.7)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(OUT / filename.replace('.csv', '_plot.png'), dpi=300, bbox_inches='tight')
            plt.close()
    
    # Race/ethnicity
    race_files = [
        ("ed_bounceback_by_race.csv", "ED Revisit by Race", '#e74c3c'),
        ("readmit_by_race.csv", "Bounce Back Admission by Race", '#3498db')
    ]
    
    for filename, title, color in race_files:
        filepath = CSV_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0)
            
            # Create figure with extra space for labels
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Create bars using range positions
            x_positions = range(len(df))
            bars = ax.bar(x_positions, df['rate']*100, color=color, alpha=0.7)
            
            ax.set_title(title, fontweight='bold', fontsize=14)
            ax.set_ylabel('Rate (%)', fontsize=12)
            ax.set_xlabel('Race', fontsize=12)
            
            # Set x-ticks and labels
            ax.set_xticks(x_positions)
            
            # Create shorter labels for better readability
            short_labels = []
            for race in df.index:
                if len(race) > 20:  # Shorten very long names
                    if "American Indian" in race:
                        short_labels.append("American Indian/\nAlaska Native")
                    elif "Native Hawaiian" in race:
                        short_labels.append("Native Hawaiian/\nPacific Islander")
                    elif "Black or African American" in race:
                        short_labels.append("Black or\nAfrican American")
                    elif "Hispanic or Latino" in race:
                        short_labels.append("Hispanic\nor Latino")
                    else:
                        short_labels.append(race[:15] + "...")
                else:
                    short_labels.append(race)
            
            ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=10)
            
            # Add value labels on bars
            for i, (bar, rate) in enumerate(zip(bars, df['rate']*100)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{rate:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                # Add sample size at bottom
                n_cases = int(df.iloc[i]['n'])
                n_total = int(df.iloc[i]['d'])
                ax.text(bar.get_x() + bar.get_width()/2., -max(df['rate']*100)*0.08,
                       f'n={n_cases}/{n_total}', ha='center', va='top', 
                       fontsize=8, alpha=0.7)
            
            # Adjust layout to prevent label cutoff
            plt.subplots_adjust(bottom=0.25)
            plt.tight_layout()
            plt.savefig(OUT / filename.replace('.csv', '_plot.png'), dpi=300, bbox_inches='tight')
            plt.close()
    
    # Sex
    sex_files = [
        ("ed_bounceback_by_sex.csv", "ED Revisit by Sex", '#e74c3c'),
        ("readmit_by_sex.csv", "Bounce Back Admission by Sex", '#3498db')
    ]
    
    for filename, title, color in sex_files:
        filepath = CSV_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(df.index, df['rate']*100, color=color, alpha=0.7)
            ax.set_title(title, fontweight='bold')
            ax.set_ylabel('Rate (%)')
            ax.set_xlabel('Sex')
            
            # Add value labels
            for bar, rate in zip(bars, df['rate']*100):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{rate:.1f}%', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(OUT / filename.replace('.csv', '_plot.png'), dpi=300, bbox_inches='tight')
            plt.close()

def plot_diagnosis_analysis():
    """Plot diagnosis-based analysis with meaningful sample sizes and descriptions"""
    diag_files = [
        ("ed_bounceback_by_diagnosis.csv", "ED Revisit by Diagnosis", '#e74c3c'),
        ("readmit_by_diagnosis.csv", "Bounce Back Admission by Diagnosis", '#3498db')
    ]
    
    # Try to load diagnosis descriptions
    diagnosis_map = {}
    try:
        diag_df = pd.read_csv("data/diagnosis.csv")
        # Create mapping from code to title, taking first occurrence of each code
        diagnosis_map = diag_df.drop_duplicates('icd_code').set_index('icd_code')['icd_title'].to_dict()
        print(f"Loaded {len(diagnosis_map)} diagnosis descriptions")
    except:
        print("Could not load diagnosis descriptions, using codes only")
    
    for filename, title, color in diag_files:
        filepath = CSV_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0)
            
            # Filter for meaningful sample sizes (at least 10 total cases and at least 2 events)
            df_filtered = df[(df['d'] >= 10) & (df['n'] >= 2)].copy()
            
            if len(df_filtered) == 0:
                print(f"No diagnoses with adequate sample size for {filename}")
                continue
            
            # Add diagnosis descriptions if available
            if diagnosis_map:
                df_filtered['description'] = df_filtered.index.map(diagnosis_map)
                # Use description if available, otherwise use code
                df_filtered['display_name'] = df_filtered.apply(
                    lambda row: row['description'] if pd.notna(row['description']) else row.name, axis=1
                )
                # Truncate long descriptions
                df_filtered['display_name'] = df_filtered['display_name'].apply(
                    lambda x: x[:50] + "..." if len(str(x)) > 50 else str(x)
                )
            else:
                df_filtered['display_name'] = df_filtered.index.astype(str)
            
            # Sort by rate (descending) and take top 15 for readability
            df_sorted = df_filtered.sort_values('rate', ascending=False).head(15)
            
            fig, ax = plt.subplots(figsize=(16, 10))
            bars = ax.barh(range(len(df_sorted)), df_sorted['rate']*100, color=color, alpha=0.7)
            ax.set_title(f'{title} (Top 15, min 10 cases, min 2 events)', fontweight='bold', fontsize=14)
            ax.set_xlabel('Rate (%)', fontsize=12)
            ax.set_ylabel('Diagnosis', fontsize=12)
            ax.set_yticks(range(len(df_sorted)))
            ax.set_yticklabels(df_sorted['display_name'], fontsize=10)
            
            # Add value labels with sample sizes
            for i, (idx, row) in enumerate(df_sorted.iterrows()):
                rate = row['rate'] * 100
                n_events = int(row['n'])
                n_total = int(row['d'])
                
                ax.text(rate + 1, i, f'{rate:.1f}% ({n_events}/{n_total})', 
                       ha='left', va='center', fontsize=9, fontweight='bold')
            
            # Add summary text
            total_diagnoses = len(df)
            filtered_diagnoses = len(df_filtered)
            ax.text(0.02, 0.98, f'Showing top 15 of {filtered_diagnoses} diagnoses\n(≥10 cases, ≥2 events)\nTotal diagnoses: {total_diagnoses}', 
                   transform=ax.transAxes, va='top', ha='left', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(OUT / filename.replace('.csv', '_plot.png'), dpi=300, bbox_inches='tight')
            plt.close()

def create_summary_dashboard():
    """Create a summary dashboard with key metrics"""
    # Try to load the overlap data for overall rates
    overall_rates = {}
    
    if (CSV_DIR / "overlap_standard.csv").exists():
        df_overlap = pd.read_csv(CSV_DIR / "overlap_standard.csv")
        total_visits = df_overlap['count'].sum()
        
        ed_revisit_rate = (df_overlap[df_overlap['category'].isin(['both', 'ed_only'])]['count'].sum() / total_visits) * 100
        readmit_rate = (df_overlap[df_overlap['category'].isin(['both', 'admit_only'])]['count'].sum() / total_visits) * 100
        both_rate = (df_overlap[df_overlap['category'] == 'both']['count'].sum() / total_visits) * 100
        
        overall_rates['ED Revisit'] = ed_revisit_rate
        overall_rates['Bounce back'] = readmit_rate
        overall_rates['Both'] = both_rate
        overall_rates['Total Visits'] = total_visits
    
    # Create dashboard
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 4, height_ratios=[1, 2, 2], hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('ED Revisit and Bounce Back Admission Analysis Dashboard', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Overall metrics (top row)
    if overall_rates:
        ax_metrics = fig.add_subplot(gs[0, :])
        ax_metrics.axis('off')
        
        metrics_text = f"""
        Total ED Discharges Analyzed: {int(overall_rates['Total Visits']):,}
        ED Revisit Rate: {overall_rates['ED Revisit']:.1f}%
        Hospital Bounce Back Rate: {overall_rates['Bounce back']:.1f}%
        Both (Overlap) Rate: {overall_rates['Both']:.1f}%
        """
        
        ax_metrics.text(0.5, 0.5, metrics_text, transform=ax_metrics.transAxes,
                       ha='center', va='center', fontsize=12, 
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3))
    
    # Load and plot mini-charts for demographic breakdowns
    plot_positions = [(1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)]
    
    # Files to include in dashboard
    dashboard_files = [
        ("ed_bounceback_by_age.csv", "ED Revisit by Age"),
        ("readmit_by_age.csv", "Bounce Back Admission by Age"),
        ("ed_bounceback_by_race.csv", "ED Revisit by Race"),
        ("readmit_by_race.csv", "Bounce Back Admission by Race"),
        ("ed_bounceback_by_sex.csv", "ED Revisit by Sex"),
        ("readmit_by_sex.csv", "Bounce Back Admission by Sex"),
    ]
    
    for i, (filename, title) in enumerate(dashboard_files[:6]):
        if i < len(plot_positions):
            row, col = plot_positions[i]
            filepath = CSV_DIR / filename
            
            if filepath.exists():
                df = pd.read_csv(filepath, index_col=0)
                ax = fig.add_subplot(gs[row, col])
                
                colors = ['#e74c3c' if 'ed_bounceback' in filename else '#3498db']
                bars = ax.bar(range(len(df)), df['rate']*100, color=colors[0], alpha=0.7)
                ax.set_title(title, fontsize=10, fontweight='bold')
                ax.set_ylabel('Rate (%)', fontsize=8)
                
                # Better x-labels handling for race data in dashboard
                if 'race' in filename:
                    ax.set_xticks(range(len(df)))
                    # Create very short labels for race categories
                    short_labels = []
                    for race in df.index:
                        if "American Indian" in race:
                            short_labels.append("AI/AN")
                        elif "Native Hawaiian" in race:
                            short_labels.append("NH/PI")  
                        elif "Black or African American" in race:
                            short_labels.append("Black")
                        elif "Hispanic or Latino" in race:
                            short_labels.append("Hispanic")
                        elif race == "White":
                            short_labels.append("White")
                        elif race == "Asian":
                            short_labels.append("Asian")
                        elif race == "Other":
                            short_labels.append("Other")
                        elif race == "Unknown":
                            short_labels.append("Unknown")
                        else:
                            short_labels.append(race[:6])
                    ax.set_xticklabels(short_labels, fontsize=7, rotation=45, ha='right')
                elif len(df) <= 3:
                    ax.set_xticks(range(len(df)))
                    ax.set_xticklabels(df.index, fontsize=7, rotation=45)
                else:
                    ax.set_xticks([0, len(df)-1])
                    ax.set_xticklabels([df.index[0], df.index[-1]], fontsize=7)
                
                # Add max value label
                max_idx = df['rate'].idxmax()
                max_val = df['rate'].max() * 100
                ax.text(0.5, 0.9, f'Max: {max_val:.1f}%\n({max_idx})', 
                       transform=ax.transAxes, ha='center', va='top', fontsize=7,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    plt.savefig(OUT / "bounce_back_dashboard.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_seasonal_heatmap():
    """Create seasonal heatmap of bounce-back rates"""
    ed_monthly = CSV_DIR / "ed_bounceback_monthly.csv"
    
    if ed_monthly.exists():
        df = pd.read_csv(ed_monthly)
        
        # Extract year and month
        df['year'] = df['month'].str[:4].astype(int)
        df['month_num'] = df['month'].str[5:7].astype(int)
        
        # Create pivot table for heatmap
        pivot_data = df.pivot(index='year', columns='month_num', values='rate')
        pivot_data_pct = pivot_data * 100
        
        # Only show recent years for better visualization
        if len(pivot_data_pct) > 10:
            pivot_data_pct = pivot_data_pct.tail(10)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create heatmap using seaborn for better handling
        sns.heatmap(pivot_data_pct, annot=True, fmt='.1f', cmap='YlOrRd', 
                   cbar_kws={'label': 'ED Revisit Rate (%)'}, ax=ax)
        
        # Set labels - let seaborn handle the ticks automatically
        ax.set_title('Seasonal Pattern of ED Revisit Rates', fontweight='bold', fontsize=14)
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        
        # Manually set month labels
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Only set labels for columns that exist
        existing_months = [month_labels[int(col)-1] for col in pivot_data_pct.columns if not pd.isna(col)]
        ax.set_xticklabels(existing_months, rotation=0)
        
        plt.tight_layout()
        plt.savefig(OUT / "seasonal_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Main function to generate all visualizations"""
    print("Generating bounce-back analysis visualizations...")
    
    # Create output directory if it doesn't exist
    OUT.mkdir(exist_ok=True)
    
    try:
        # Generate all plots based
        load_and_plot_overlap()
        print("✓ Overlap visualizations created")
        
        plot_time_trends()
        print("✓ Time trend plots created")
        
        plot_demographic_comparisons()
        print("✓ Demographic comparison plots created")
        
        plot_diagnosis_analysis()
        print("✓ Diagnosis analysis plots created")
        
        plot_seasonal_heatmap()
        print("✓ Seasonal heatmap created")
        
        create_summary_dashboard()
        print("✓ Summary dashboard created")
        
        print(f"\nAll visualizations saved to: {OUT.absolute()}")
        
        # List all generated files
        plot_files = list(OUT.glob("*.png"))
        if plot_files:
            print("\nGenerated plots:")
            for f in sorted(plot_files):
                if f.name.endswith('.png'):
                    print(f"  - {f.name}")
    
    except Exception as e:
        print(f"Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
