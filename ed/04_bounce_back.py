import pandas as pd

# Load ED stays with admission metadata
edstays = pd.read_csv('edstays.csv', parse_dates=['intime', 'outtime'])

# Sort by subject and intime
edstays = edstays.sort_values(['subject_id', 'intime'])

# Find next ED visit for each patient
edstays['next_intime'] = edstays.groupby('subject_id')['intime'].shift(-1)
edstays['next_stay_id'] = edstays.groupby('subject_id')['stay_id'].shift(-1)

# Calculate time to next visit (in days)
edstays['days_to_next'] = (edstays['next_intime'] - edstays['outtime']).dt.total_seconds() / 86400

# Flag bounce-backs: return visit within 7 days
edstays['bounceback'] = edstays['days_to_next'].between(0.01, 7)

# Load merged ED data (with is_false_admission flag)
ed = pd.read_csv('ed_merged.csv')

# Merge bounce-back info into ED dataset
bounce_merged = pd.merge(edstays, ed[['subject_id', 'stay_id', 'is_false_admission']],
                         on=['subject_id', 'stay_id'], how='left')

# Drop rows where is_false_admission is missing
filtered_bounce_merged = bounce_merged[bounce_merged['is_false_admission'].notna()]

# Calculate bounce-back rate among false admissions
false_with_bounce = filtered_bounce_merged[
    (filtered_bounce_merged['is_false_admission']) &
    (filtered_bounce_merged['bounceback'])
]

false_total = filtered_bounce_merged[filtered_bounce_merged['is_false_admission']]
bounce_rate = false_with_bounce.shape[0] / false_total.shape[0]

print(f"Bounce-back rate among false ED admissions: {bounce_rate:.2%}")

# Save matched bounce-back subset for further analysis
false_with_bounce.to_csv('false_admissions_with_bouncebacks.csv', index=False)
print("Saved: false_admissions_with_bouncebacks.csv")
