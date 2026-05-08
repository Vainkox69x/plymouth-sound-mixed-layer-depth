"""ctd_analysis.py

Simple driver script to compute cast-by-cast statistics from Sea-Bird CNV files.

This script searches for files matching `20260311_CTD*.cnv`, parses the data
block after the `*END*` marker, filters rows with invalid salinity (<= 0.0) and
prints summary statistics (max depth, min/max/mean salinity) for each cast.

Run this from the repository root. See `README.md` for running instructions.
"""

import pandas as pd
import numpy as np
import scipy.io
import os
import glob

# Work from repository root. If you reorganise files into `data/`, adjust this.
os.chdir(r'c:\Users\PC\OneDrive\Desktop\mar_pres')

print("="*100)
print("CTD CAST-BY-CAST STATISTICS WITH CORRECTED SALINITY FILTER")
print("(Removing only rows with salinity = 0.000)")
print("="*100)

cnv_files = sorted(glob.glob("20260311_CTD*.cnv"))
print(f"\nAnalyzing {len(cnv_files)} CTD casts...\n")

print(f"{'Cast':>4} | {'File':<35} | {'Records':>6} | {'Max Depth':>10} | {'Min Sal':>8} | {'Max Sal':>8} | {'Mean Sal':>9}")
print("-" * 110)

cast_num = 0
for cnv_file in cnv_files:
    cast_num += 1
    try:
        with open(cnv_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Find *END* marker
        end_idx = None
        for i, line in enumerate(lines):
            if line.strip() == '*END*':
                end_idx = i
                break
        
        if end_idx is None:
            print(f"{cast_num:4d} | {cnv_file:<35} | ERROR - no *END* marker")
            continue
        
        # Parse data
        data_lines = lines[end_idx+1:]
        data = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    depth = float(parts[0])
                    temp = float(parts[1])
                    cond = float(parts[2])
                    sal = float(parts[3])
                    data.append([depth, temp, cond, sal])
                except:
                    pass
        
        if len(data) == 0:
            print(f"{cast_num:4d} | {cnv_file:<35} | ERROR - no data")
            continue
        
        data = np.array(data)
        
        # Apply filter: remove only salinity <= 0.0
        valid = data[:, 3] > 0.0
        data_filtered = data[valid]
        rows_removed = len(data) - len(data_filtered)
        
        if len(data_filtered) == 0:
            print(f"{cast_num:4d} | {cnv_file:<35} | ERROR - all rows removed")
            continue
        
        # Get statistics
        max_depth = data_filtered[:, 0].max()
        min_sal = data_filtered[:, 3].min()
        max_sal = data_filtered[:, 3].max()
        mean_sal = data_filtered[:, 3].mean()
        
        print(f"{cast_num:4d} | {cnv_file:<35} | {len(data_filtered):6d} | {max_depth:10.2f} | {min_sal:8.4f} | {max_sal:8.4f} | {mean_sal:9.4f}")
        
    except Exception as e:
        print(f"{cast_num:4d} | {cnv_file:<35} | ERROR: {str(e)[:40]}")

print("\n" + "="*100)
