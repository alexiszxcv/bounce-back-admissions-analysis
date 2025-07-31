import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load full merged dataset
ed_merged = pd.read_csv('ed_merged.csv')

# Style
sns.set_context("paper", font_scale=1.4)
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'serif'

# Violin plot: Heart rate comparison
plt.figure(figsize=(8, 5))
sns.violinplot(data=ed_merged, x='is_false_admission', y='heartrate', palette='Set2', inner='box')
plt.xticks([0, 1], ['Normal ED Stay', 'False Admission'])
plt.ylabel('Heart Rate (bpm)')
plt.title('Heart Rate Distribution by Admission Type')
plt.tight_layout()
plt.savefig('violin_heartrate_false_vs_normal.png', dpi=300)
plt.show()

# Flag abnormal vitals
ed_merged['tachycardia'] = ed_merged['heartrate'] > 100
ed_merged['hypoxia'] = ed_merged['o2sat'] < 92

# Proportion with abnormal vitals
abnormal_vitals = ed_merged.groupby('is_false_admission')[['tachycardia', 'hypoxia']].mean().reset_index()
abnormal_vitals['is_false_admission'] = abnormal_vitals['is_false_admission'].map({True: 'False Admission', False: 'Normal ED Stay'})

# Bar plot
abnormal_vitals.set_index('is_false_admission').T.plot(kind='bar', figsize=(8, 5), color=['#66c2a5', '#fc8d62'])
plt.ylabel('Proportion with Abnormal Vital Sign')
plt.title('Abnormal Vitals in False vs Normal ED Stays')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('bar_abnormal_vitals_by_group.png', dpi=300)
plt.show()

# Stacked bar: disposition by group
disp_ct = ed_merged.groupby(['disposition', 'is_false_admission']).size().unstack().fillna(0)
disp_ct_norm = disp_ct.div(disp_ct.sum(axis=1), axis=0)

disp_ct_norm.plot(kind='barh', stacked=True, figsize=(8, 6), color=['#8da0cb', '#fc8d62'])
plt.xlabel('Proportion')
plt.title('Disposition Type by False vs Normal ED Admission')
plt.tight_layout()
plt.savefig('stacked_disposition_by_group.png', dpi=300)
plt.show()
