import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load diagnosis and ED merged data
dx = pd.read_csv('diagnosis.csv')  # or 'diagnoses_icd.csv'
ed = pd.read_csv('ed_merged.csv')
bounces = pd.read_csv('false_admissions_with_bouncebacks.csv')

# Step 1: Prepare diagnosis codes
dx['icd_prefix'] = dx['icd_code'].astype(str).str[:3]

# Step 2: Filter to only false admissions
false_admits = ed[ed['is_false_admission'] & ed['stay_id'].notna()]
false_admits = false_admits[['subject_id', 'stay_id', 'hadm_id']].dropna()

# Step 3: Join diagnoses for false admissions
dx_false = pd.merge(dx, false_admits, on='stay_id', how='inner')

# Step 4: Get top ICD code groups among false admits
top_icd = dx_false['icd_prefix'].value_counts().head(10).index.tolist()
top_dx_false = dx_false[dx_false['icd_prefix'].isin(top_icd)]

# Step 5: Join bounce-back info
bounces['bounceback'] = True
false_admits = false_admits.merge(bounces[['subject_id', 'stay_id', 'bounceback']],
                                   on=['subject_id', 'stay_id'], how='left')
false_admits['bounceback'] = false_admits['bounceback'].fillna(False)

# Step 6: Merge ICD prefix info into false_admits
icd_labels = dx_false[['hadm_id', 'icd_prefix']].drop_duplicates()
false_annotated = pd.merge(false_admits, icd_labels, on='hadm_id', how='left')
false_annotated = false_annotated[false_annotated['icd_prefix'].isin(top_icd)]

# Step 7: Calculate bounce-back rate per top ICD prefix
summary = false_annotated.groupby('icd_prefix')['bounceback'].agg(['count', 'sum']).reset_index()
summary['bounce_rate'] = summary['sum'] / summary['count']

# Step 8: Map ICD prefixes to human-readable descriptions
icd_description_map = {
    '789': 'Abdominal pain (ICD-9)',
    '786': 'Chest pain, breathing issues',
    '780': 'General symptoms (fever, etc.)',
    '250': 'Diabetes-related problems',
    'R07': 'Chest pain (ICD-10)',
    '401': 'Hypertension',
    'R41': 'Cognitive disturbances',
    'R10': 'Abdominal pain (ICD-10)',
    'E88': 'Metabolic disorders',
    'R06': 'Shortness of breath'
}
summary['description'] = summary['icd_prefix'].map(icd_description_map)
summary = summary[['icd_prefix', 'description', 'count', 'sum', 'bounce_rate']]
summary.columns = ['ICD Prefix', 'Description', 'Count of False Admissions', 'Bounce-Backs', 'Bounce-Back Rate']

# Save CSV
summary.to_csv('top_diagnosis_bounceback_summary_cleaned.csv', index=False)

# ---- Clean Visualizations ----
sns.set_context("paper", font_scale=1.4)
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'serif'

# Convert bounce rate to %
summary['Bounce-Back Rate (%)'] = (summary['Bounce-Back Rate'] * 100).round(2)

# Plot 1: Bounce-back rate by diagnosis
plt.figure(figsize=(10, 6))
sns.barplot(
    data=summary.sort_values('Bounce-Back Rate (%)', ascending=False),
    x='Bounce-Back Rate (%)',
    y='Description',
    palette='coolwarm'
)
plt.xlabel('Bounce-Back Rate (%)')
plt.ylabel('Diagnosis Group')
plt.title('Top Diagnosis Groups by Bounce-Back Rate (False ED Admissions)')
plt.tight_layout()
plt.savefig('bounceback_rate_by_diagnosis.png', dpi=300)
plt.show()

# Plot 2: Number of false admissions by diagnosis
plt.figure(figsize=(10, 6))
sns.barplot(
    data=summary.sort_values('Count of False Admissions', ascending=False),
    x='Count of False Admissions',
    y='Description',
    palette='crest'
)
plt.xlabel('Count of False Admissions')
plt.ylabel('Diagnosis Group')
plt.title('Most Common Diagnoses in False ED Admissions')
plt.tight_layout()
plt.savefig('false_admission_count_by_diagnosis.png', dpi=300)
plt.show()
