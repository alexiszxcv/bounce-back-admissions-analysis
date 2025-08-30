import pandas as pd

edstays = pd.read_csv('data/edstays.csv', parse_dates=['intime', 'outtime'])
vitals = pd.read_csv('data/vitalsign.csv', parse_dates=['charttime'])

# Calculate ED length of stay and flag false admissions
edstays['ed_los_hours'] = (edstays['outtime'] - edstays['intime']).dt.total_seconds() / 3600
edstays['is_false_admission'] = edstays['ed_los_hours'] <= 12

# Merge vitals with ED stay metadata
vitals_merged = pd.merge(
    vitals,
    edstays[['subject_id', 'stay_id', 'intime', 'outtime', 'is_false_admission']],
    on=['subject_id', 'stay_id'],
    how='inner'
)

# Filter vitals within stay window
vitals_clean = vitals_merged[
    (vitals_merged['charttime'] >= vitals_merged['intime']) &
    (vitals_merged['charttime'] <= vitals_merged['outtime'])
]

# Convert to numeric
vital_cols = ['temperature', 'heartrate', 'resprate', 'o2sat', 'sbp', 'dbp', 'pain']
for col in vital_cols:
    vitals_clean[col] = pd.to_numeric(vitals_clean[col], errors='coerce')

# Aggregate vitals
vital_summary = vitals_clean.groupby(['subject_id', 'stay_id'])[vital_cols].mean().reset_index()

# Merge vitals into full ED data
ed_merged = pd.merge(edstays, vital_summary, on=['subject_id', 'stay_id'], how='left')

# Filter out implausible values
ed_merged = ed_merged[
    (ed_merged['temperature'] >= 93) & (ed_merged['temperature'] <= 108) &
    (ed_merged['heartrate'] >= 30) & (ed_merged['heartrate'] <= 200) &
    (ed_merged['o2sat'] >= 50) & (ed_merged['o2sat'] <= 100)
]

# Save full merged dataset
ed_merged.to_csv('ed_merged.csv', index=False)
print("Saved: ed_merged.csv")
