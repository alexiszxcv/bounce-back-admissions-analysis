import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load cleaned data
ed_merged = pd.read_csv('ed_merged.csv')

# Filter false admissions
filtered = ed_merged[ed_merged['is_false_admission']]

# Set publication style
sns.set_context("paper", font_scale=1.5)
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'serif'

# Plotting function
def plot_clinical_dist(df, col, bounds=None, xlabel=None):
    plt.figure(figsize=(8, 5))
    sns.histplot(df[col].dropna(), kde=True, bins=40, color='steelblue', edgecolor='black')
    if bounds:
        for b in bounds:
            plt.axvline(x=b, color='red', linestyle='--', linewidth=1.2, label=f'Threshold: {b}')
    plt.title(f'Distribution of {col}', fontsize=16)
    plt.xlabel(xlabel if xlabel else col)
    plt.ylabel("Number of Visits")
    if bounds:
        plt.legend()
    plt.tight_layout()
    plt.savefig(f'{col}_distribution_cleaned.png', dpi=300)
    plt.show()

# Visualizations
plot_clinical_dist(filtered, 'ed_los_hours', xlabel='ED Length of Stay (hours)')
plot_clinical_dist(filtered, 'temperature', bounds=[95, 100.4], xlabel='Temperature (°F)')
plot_clinical_dist(filtered, 'heartrate', bounds=[60, 100], xlabel='Heart Rate (bpm)')
plot_clinical_dist(filtered, 'o2sat', bounds=[92], xlabel='Oxygen Saturation (%)')

# Save filtered false admissions
filtered.to_csv('false_ed_with_cleaned_vitals.csv', index=False)
print("Saved: false_ed_with_cleaned_vitals.csv")