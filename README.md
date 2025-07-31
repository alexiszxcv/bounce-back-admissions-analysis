# False ED Admissions Analysis

This repository contains scripts and figures for analyzing false emergency department (ED) admissions and associated bounce-back patterns.

## Structure

- `src/` – Python scripts for data processing and analysis  
- `data/` – CSV data files (excluded from GitHub due to size)  
- `figures/` – Generated plots for visualizations  
- `requirements.txt` – Python dependencies

## Key Scripts

- `01_clean_merge_data.py` – Cleans and merges raw datasets  
- `02_visualize_false_admissions.py` – Plots distributions of false admissions  
- `03_compare_false_vs_normal.py` – Compares metrics between false and true admissions  
- `04_bounce_back.py` – Analyzes 72-hour bounce-back events  
- `05_diagnosis_analysis.py` – Breaks down patterns by diagnosis

