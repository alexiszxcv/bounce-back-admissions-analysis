# src/04_bounce_back.py

import os
import pandas as pd
from pathlib import Path


DATA = Path(os.environ.get("DATA_DIR", "data"))
OUT = Path("figures"); OUT.mkdir(parents=True, exist_ok=True)
CSV_OUT = Path("csv_outputs"); CSV_OUT.mkdir(parents=True, exist_ok=True)

# window for bounce-backs / readmissions
W_DAYS = int(os.environ.get("W_DAYS", 3))          
# clock tolerance for tiny negative drifts between sources (minutes)
TOL_MINUTES = int(os.environ.get("TOL_MINUTES", 10))
# whether to compute the strict "both = revisit -> admit" definition
STRICT_BOTH = os.environ.get("STRICT_BOTH", "1") not in {"0","false","False"}

def read_table(basename, parse_dates=None, usecols=None, required=True):
    """
    Read DATA/{basename}.csv.gz if present, else .csv.
    """
    gz = DATA / f"{basename}.csv.gz"
    cs = DATA / f"{basename}.csv"
    path = gz if gz.exists() else cs if cs.exists() else None
    if path is None:
        msg = f"Missing file: {gz} or {cs}. Set DATA_DIR or place files in ./data/"
        if required:
            raise FileNotFoundError(msg)
        print("WARN:", msg)
        return None
    return pd.read_csv(path, parse_dates=parse_dates, usecols=usecols)

# Load data
ed  = read_table("edstays",   parse_dates=["intime","outtime"])
tri = read_table("triage",    required=False)
dx  = read_table("diagnosis", required=False)
adm = read_table("admissions",
                 parse_dates=["admittime","dischtime"],
                 usecols=["subject_id","hadm_id","admittime","dischtime"],
                 required=False)

# Merge optional tables
df = ed.merge(tri, on="stay_id", how="left") if tri is not None else ed.copy()
if dx is not None:
    dx1 = dx.sort_values(["stay_id"]).drop_duplicates("stay_id")
    df = df.merge(dx1, on="stay_id", how="left")

# See if expected columns exist
if "hadm_id" not in df.columns:
    df["hadm_id"] = pd.NA

def clean_race_column(df):
    """
    Clean and standardize race data into major racial categories.
    Groups ethnicity-specific entries into broader race categories.
    """
    if "race" not in df.columns:
        return df
    
    # Create copy to avoid modifying original
    df = df.copy()
    
    # Define race mapping - group by major racial categories
    race_mapping = {
        # White categories
        'WHITE': 'White',
        'WHITE - OTHER EUROPEAN': 'White', 
        'WHITE - RUSSIAN': 'White',
        'WHITE - BRAZILIAN': 'White',
        'WHITE - EASTERN EUROPEAN': 'White',
        'PORTUGUESE': 'White',  
        
        # Black/African American categories  
        'BLACK/AFRICAN AMERICAN': 'Black or African American',
        'BLACK/AFRICAN': 'Black or African American',
        'BLACK/CAPE VERDEAN': 'Black or African American',
        'BLACK/CARIBBEAN ISLAND': 'Black or African American',
        
        # Asian categories
        'ASIAN': 'Asian',
        'ASIAN - CHINESE': 'Asian',
        'ASIAN - ASIAN INDIAN': 'Asian', 
        'ASIAN - SOUTH EAST ASIAN': 'Asian',
        'ASIAN - KOREAN': 'Asian',
        
        # Hispanic/Latino - group as single category (can be any race)
        'HISPANIC/LATINO - PUERTO RICAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - DOMINICAN': 'Hispanic or Latino',
        'HISPANIC OR LATINO': 'Hispanic or Latino',
        'HISPANIC/LATINO - GUATEMALAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - SALVADORAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - COLUMBIAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - MEXICAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - HONDURAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - CUBAN': 'Hispanic or Latino',
        'HISPANIC/LATINO - CENTRAL AMERICAN': 'Hispanic or Latino',
        'SOUTH AMERICAN': 'Hispanic or Latino',  
        
        # Native American
        'AMERICAN INDIAN/ALASKA NATIVE': 'American Indian or Alaska Native',
        
        # Pacific Islander
        'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER': 'Native Hawaiian or Pacific Islander',
        
        # Other/Multiple/Unknown
        'OTHER': 'Other',
        'MULTIPLE RACE/ETHNICITY': 'Other',
        'UNKNOWN': 'Unknown',
        'UNABLE TO OBTAIN': 'Unknown', 
        'PATIENT DECLINED TO ANSWER': 'Unknown'
    }
    
    # Apply the mapping
    df['race_cleaned'] = df['race'].map(race_mapping)
    
    # Handle any unmapped values
    unmapped = df[df['race_cleaned'].isna() & df['race'].notna()]['race'].unique()
    if len(unmapped) > 0:
        print(f"Warning: Unmapped race values found: {unmapped}")
        # Map unmapped values to 'Other'
        df.loc[df['race_cleaned'].isna() & df['race'].notna(), 'race_cleaned'] = 'Other'
    
    # Replace original race column
    df['race'] = df['race_cleaned']
    df = df.drop('race_cleaned', axis=1)
    
    return df

# Clean race data
print("Cleaning race data...")
df = clean_race_column(df)
if "race" in df.columns:
    race_counts = df['race'].value_counts()
    print(f"Race categories after cleaning: {len(race_counts)}")
    for race, count in race_counts.items():
        print(f"  {race}: {count:,}")
    print()

# Build robust index cohort (true ED discharges)
# Focus on ED visits that did NOT result in hospital admission
not_admitted_from_ed = df["hadm_id"].isna()
has_outtime = df["outtime"].notna()

# Optional outcome text columns (use whatever exist)
text_cols = [c for c in ["disposition","edoutcome","outcome","ed_disposition"] if c in df.columns]

# Exclude obvious non-discharges if text available: AMA/LWBS/eloped/transfer/death/hospice
exclude_pat = r"ama|left\s*without|lwbs|elope|transfer|expired|death|deceased|died|hospice"
if text_cols:
    bad_outcome = False
    for c in text_cols:
        bad_outcome = bad_outcome | df[c].astype(str).str.contains(exclude_pat, case=False, na=False)
else:
    bad_outcome = False  # no text to exclude

idx = df[not_admitted_from_ed & has_outtime & ~bad_outcome].copy()

# QA: cohort construction
print("\n[QA] index cohort (true ED discharges)")
print(f"DATA_DIR={os.environ.get('DATA_DIR','data')}  W_DAYS={W_DAYS}  TOL_MINUTES={TOL_MINUTES}  STRICT_BOTH={STRICT_BOTH}")
print(f"all ED rows:                              {len(df):,}")
print(f"hadm_id is NA (not admitted from ED):     {not_admitted_from_ed.sum():,}")
print(f"has outtime:                              {has_outtime.sum():,}")
if text_cols:
    print(f"excluded via outcome text ({', '.join(text_cols)}): {int(bad_outcome.sum()):,}")
print(f"INDEX DISCHARGES USED (idx):              {len(idx):,}\n")

# A) ED BOUNCE-BACK (ED revisit within W_DAYS)
# Sort by subject_id and outtime to get proper discharge sequence
idx = idx.sort_values(["subject_id","outtime"])

# For each ED discharge, find the next ED arrival that occurs AFTER the discharge
def find_next_ed_visit(group):
    group = group.sort_values("outtime")
    group["returned_W"] = False
    
    for i in range(len(group)):
        current_outtime = group.iloc[i]["outtime"]
        # Look for future visits (after current discharge)
        future_visits = group[group["intime"] > current_outtime]
        if not future_visits.empty:
            next_visit_time = future_visits["intime"].min()
            days_to_next = (next_visit_time - current_outtime).total_seconds() / 86400.0
            if 0 <= days_to_next <= W_DAYS:
                group.iloc[i, group.columns.get_loc("returned_W")] = True
    return group

idx = idx.groupby("subject_id").apply(find_next_ed_visit).droplevel(0)

den_ed_revisit = len(idx)
num_ed_revisit = int(idx["returned_W"].sum())
rate_ed_revisit = (num_ed_revisit / den_ed_revisit) if den_ed_revisit else float("nan")
print(f"[ED revisit rate] overall {W_DAYS}d: {rate_ed_revisit:.2%} (n={num_ed_revisit}/{den_ed_revisit})")

# B) Inpatient readmission (new hadm_id within W_DAYS)
# with CLOCK TOLERANCE for minor negative drift
if adm is not None:
    adm_min = adm.dropna(subset=["admittime"])[["subject_id","hadm_id","admittime","dischtime"]].copy()

    # For each index ED discharge, find earliest admission after outtime within window
    join = idx[["subject_id","stay_id","outtime"]].merge(adm_min, on="subject_id", how="left")
    # allow tiny negative drift (e.g., -10 minutes)
    valid = join["admittime"].notna() & ((join["admittime"] - join["outtime"]) >= pd.Timedelta(minutes=-TOL_MINUTES))
    join = join[valid].copy()
    join["days_to_admit"] = (join["admittime"] - join["outtime"]).dt.total_seconds() / 86400.0
    # Apply the window filter, but respect the tolerance for slightly negative times
    join = join[join["days_to_admit"].between(-TOL_MINUTES/1440.0, W_DAYS)]  # convert minutes to days

    earliest = (join.sort_values(["stay_id","admittime"])
                    .drop_duplicates("stay_id", keep="first"))

    idx["readmit_W"] = idx["stay_id"].isin(earliest["stay_id"])
else:
    idx["readmit_W"] = False  # admissions not available

den_bounceback = len(idx)
num_bounceback = int(idx["readmit_W"].sum())
rate_bounceback = (num_bounceback / den_bounceback) if den_bounceback else float("nan")
print(f"[Bounce-back rate] overall {W_DAYS}d after ED discharge: {rate_bounceback:.2%} (n={num_bounceback}/{den_bounceback})")

# C) Overlap: ED revisit vs bounce-back (hospital readmission)
# (standard overlap and optional STRICT "revisit -> admit")
# Standard overlap (as before)
both_std    = int((idx["returned_W"] &  idx["readmit_W"]).sum())  # Both ED revisit and bounce-back
ed_only_std = int((idx["returned_W"] & ~idx["readmit_W"]).sum())  # ED revisit only
bb_only_std = int((~idx["returned_W"] &  idx["readmit_W"]).sum()) # Bounce-back only
neither_std = int((~idx["returned_W"] & ~idx["readmit_W"]).sum()) # Neither event
den = len(idx)

print(f"\noverlap within {W_DAYS}d (standard, n={den}):")
print(f"  both (ed revisit + admit): {both_std} ({(both_std/den):.2%})")
print(f"  ed revisit only:           {ed_only_std} ({(ed_only_std/den):.2%})")
print(f"  bounce-back only:           {bb_only_std} ({(bb_only_std/den):.2%})")
print(f"  neither:                   {neither_std} ({(neither_std/den):.2%})")

# Strict "both": admission must occur AFTER the ED revisit arrival
# For the strict definition, we need to find the actual next ED visit time for those who returned
if STRICT_BOTH and adm is not None:
    # For patients who had an ED revisit, find the actual time of their next visit
    revisit_times = []
    
    for _, row in idx[idx["returned_W"]].iterrows():
        subject_id = row["subject_id"]
        current_outtime = row["outtime"]
        
        # Find future ED visits for this patient after current discharge
        future_visits = idx[(idx["subject_id"] == subject_id) & 
                           (idx["intime"] > current_outtime)]
        
        if not future_visits.empty:
            next_visit_time = future_visits["intime"].min()
            revisit_times.append({
                "subject_id": subject_id,
                "stay_id": row["stay_id"], 
                "next_intime": next_visit_time
            })
    
    if revisit_times:
        rev_df = pd.DataFrame(revisit_times)
        
        # Join to the admissions that are already after outtime and within W_DAYS
        j_strict = rev_df.merge(
            join[["subject_id","stay_id","admittime"]],
            on=["subject_id","stay_id"],
            how="left"
        )
        # admission must be on/after the revisit arrival
        j_strict = j_strict[j_strict["admittime"].notna() & 
                           (j_strict["admittime"] >= j_strict["next_intime"])]
        
        # keep earliest admission per index stay (in case of multiple)
        j_strict = j_strict.sort_values(["stay_id","admittime"]).drop_duplicates("stay_id", keep="first")
        
        both_strict = int(j_strict["stay_id"].nunique())
    else:
        both_strict = 0
    ed_only_strict = int(idx["returned_W"].sum() - both_strict)
    adm_only_strict = int((~idx["returned_W"] & idx["readmit_W"]).sum())
    neither_strict  = int(len(idx) - (both_strict + ed_only_strict + adm_only_strict))

    print(f"\noverlap within {W_DAYS}d (STRICT revisit→admit, n={len(idx)}):")
    print(f"  both (revisit then admit): {both_strict} ({(both_strict/len(idx)):.2%})")
    print(f"  ed revisit only:           {ed_only_strict} ({(ed_only_strict/len(idx)):.2%})")
    print(f"  admit only:                {adm_only_strict} ({(adm_only_strict/len(idx)):.2%})")
    print(f"  neither:                   {neither_strict} ({(neither_strict/len(idx)):.2%})")

# Save overlap summaries
pd.DataFrame({
    "category": ["both","ed_only","admit_only","neither"],
    "count":    [both_std, ed_only_std, bb_only_std, neither_std],
    "rate":     [both_std/den if den else float("nan"),
                 ed_only_std/den if den else float("nan"),
                 bb_only_std/den if den else float("nan"),
                 neither_std/den if den else float("nan")]
}).to_csv(CSV_OUT / "overlap_standard.csv", index=False)

if STRICT_BOTH and adm is not None:
    pd.DataFrame({
        "category": ["both_strict","ed_only_strict","admit_only","neither_strict"],
        "count":    [both_strict, ed_only_strict, adm_only_strict, neither_strict],
        "rate":     [both_strict/den if den else float("nan"),
                     ed_only_strict/den if den else float("nan"),
                     adm_only_strict/den if den else float("nan"),
                     neither_strict/den if den else float("nan")]
    }).to_csv(CSV_OUT / "overlap_strict_revisit_then_admit.csv", index=False)

# D) Grouped summaries 
def group_rate(frame, flag, by, out_name):
    g = frame.groupby(by, dropna=False).agg(n=(flag,"sum"), d=(flag,"size"))
    g["rate"] = g["n"] / g["d"]
    g.to_csv(CSV_OUT / out_name)

# time trend by month of ED discharge
idx["month"] = idx["outtime"].dt.strftime("%Y-%m")
group_rate(idx, "returned_W", "month", "ed_bounceback_monthly.csv")
group_rate(idx, "readmit_W",  "month", "readmit_monthly.csv")

# age groups (if age exists)
if "age" in idx.columns:
    bins = [0,18,35,50,65,80,200]; labels = ["0-17","18-34","35-49","50-64","65-79","80+"]
    idx["age_group"] = pd.cut(idx["age"], bins=bins, labels=labels, right=False)
    group_rate(idx, "returned_W", "age_group", "ed_bounceback_by_age.csv")
    group_rate(idx, "readmit_W",  "age_group", "readmit_by_age.csv")

# sex
if "sex" in idx.columns:
    group_rate(idx, "returned_W", "sex", "ed_bounceback_by_sex.csv")
    group_rate(idx, "readmit_W",  "sex", "readmit_by_sex.csv")

# race
if "race" in idx.columns:
    group_rate(idx, "returned_W", "race", "ed_bounceback_by_race.csv")
    group_rate(idx, "readmit_W",  "race", "readmit_by_race.csv")

# by diagnosis (prefer grouped column if present)
dx_col = "icd_group" if "icd_group" in idx.columns else ("icd_code" if "icd_code" in idx.columns else None)
if dx_col:
    group_rate(idx, "returned_W", dx_col, "ed_bounceback_by_diagnosis.csv")
    group_rate(idx, "readmit_W",  dx_col, "readmit_by_diagnosis.csv")

print("\nsaved CSV summaries in csv_outputs/ (where grouping columns exist).")

# Generate visualizations
print("\nGenerating visualizations...")
try:
    import subprocess
    import sys
    
    # Run the visualization script
    result = subprocess.run([sys.executable, "src/06_visualize_bounce_back.py"], 
                          capture_output=True, text=True, cwd=".")
    
    if result.returncode == 0:
        print("✓ Visualizations generated successfully")
        if result.stdout:
            print(result.stdout)
    else:
        print("⚠ Error generating visualizations:")
        if result.stderr:
            print(result.stderr)
    
    # Generate summary report
    print("\nGenerating summary report...")
    report_result = subprocess.run([sys.executable, "src/07_generate_report.py"], 
                                 capture_output=True, text=True, cwd=".")
    
    if report_result.returncode == 0:
        print(report_result.stdout)
    else:
        print("⚠ Error generating report")
        if report_result.stderr:
            print(report_result.stderr)
        
except ImportError as e:
    print(f"⚠ Could not generate visualizations: {e}")
    print("  Install matplotlib and seaborn to enable visualization generation")
except Exception as e:
    print(f"⚠ Error running visualization script: {e}")
