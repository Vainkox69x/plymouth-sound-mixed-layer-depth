"""ctd.py

Top-level CTD processing utilities used in this coursework.

This module parses Sea-Bird CNV files (processed `_conv.cnv` files), extracts the
data block after the `*END*` marker, applies simple filtering (e.g. removing rows
with invalid salinity) and computes per-cast statistics saved for downstream plots.

Do not change runtime behaviour — this docstring only documents the file's purpose
and the major processing steps that follow below.
"""

import pandas as pd
import numpy as np
import scipy.io
import os
from datetime import datetime
import re

# -- Set working directory --------------------------------------------------
# The scripts in this repository assume running from the repository root. If you
# move files into `data/` change the working directory or adjust paths accordingly.
work_dir = r'c:\Users\PC\OneDrive\Desktop\mar_pres'
os.chdir(work_dir)

print("="*80)
print("OCEANOGRAPHIC DATA PROCESSING PIPELINE")
print(f"Working directory: {os.getcwd()}")
print("="*80)

# ============================================================================
# STEP 1: LOAD AND ANALYZE CTD PROFILES (from SeaBird CNV files)
# ============================================================================
print("\n" + "="*80)
print("STEP 1: CTD PROFILES - LOADING SEABIRD PROCESSED CNV FILES")
print("="*80)

ctd_data = {}
ctd_stats = {}

# Look for .cnv files in main directory
cnv_files = sorted([f for f in os.listdir('.') if f.endswith('_conv.cnv')])
print(f"\nFound {len(cnv_files)} processed CTD files (.cnv)")

for cast_num, cnv_file in enumerate(cnv_files, 1):
    try:
        # Read the CNV file
        with open(cnv_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Find the *END* marker
        end_line_idx = None
        for idx, line in enumerate(lines):
            if line.strip() == '*END*':
                end_line_idx = idx
                break
        
        if end_line_idx is None:
            print(f"\n[ERROR] Cast {cast_num:02d} ({cnv_file}): No *END* marker found")
            continue
        
        # Read data after *END* line
        data_lines = lines[end_line_idx + 1:]
        data_lines = [l.strip() for l in data_lines if l.strip() and not l.startswith('#')]
        
        if len(data_lines) == 0:
            print(f"\n[WARNING] Cast {cast_num:02d} ({cnv_file}): No data after *END* marker")
            continue
        
        # Parse data - 8 columns: depth, temp, conductivity, salinity, density, v0, v1, flag
        data_array = []
        for line_num, line in enumerate(data_lines):
            try:
                values = line.split()
                if len(values) >= 8:
                    data_array.append([float(v) for v in values[:8]])
            except ValueError as e:
                if line_num < 5 or line_num > len(data_lines) - 5:
                    print(f"  [DEBUG] Line {line_num}: {line[:50]}... -> parse error")
                continue
        
        if len(data_array) == 0:
            print(f"\n[ERROR] Cast {cast_num:02d} ({cnv_file}): Could not parse any data rows")
            continue
        
        data_array = np.array(data_array)
        df = pd.DataFrame(data_array, columns=['depth', 'temperature', 'conductivity', 'salinity', 'density', 'v0', 'v1', 'flag'])
        
        # Remove any rows with NaN values
        df = df.dropna()
        
        # Remove only rows where salinity is exactly 0.000 or negative (invalid measurements)
        # Keep all positive salinity values including fresh water (< 0.5 PSU)
        rows_before_filter = len(df)
        df = df[df['salinity'] > 0.0]
        rows_removed = rows_before_filter - len(df)
        
        if rows_removed > 0:
            print(f"  [INFO] Removed {rows_removed} rows with invalid salinity (≤ 0.000)")
        
        ctd_data[cast_num] = df
        
        # Calculate statistics
        stats = {
            'file': cnv_file,
            'n_records': len(df),
            'max_depth': df['depth'].max(),
            'min_temp': df['temperature'].min(),
            'max_temp': df['temperature'].max(),
            'mean_temp': df['temperature'].mean(),
            'min_sal': df['salinity'].min(),
            'max_sal': df['salinity'].max(),
            'mean_sal': df['salinity'].mean(),
            'min_dens': df['density'].min(),
            'max_dens': df['density'].max(),
            'mean_dens': df['density'].mean(),
        }
        ctd_stats[cast_num] = stats
        
        # Print cast summary
        print(f"\nCast {cast_num:02d}: {cnv_file}")
        print(f"  Records: {stats['n_records']}")
        print(f"  Depth: {stats['max_depth']:.2f} m")
        print(f"  Temp:  {stats['min_temp']:.2f} to {stats['max_temp']:.2f}C (mean {stats['mean_temp']:.2f}C)")
        print(f"  Sal:   {stats['min_sal']:.3f} to {stats['max_sal']:.3f} (mean {stats['mean_sal']:.3f})")
        print(f"  Dens:  {stats['min_dens']:.2f} to {stats['max_dens']:.2f} kg/m3")
        
        # Print first 5 rows to verify
        if cast_num == 1:
            print(f"\n  First 5 data rows of Cast 1:")
            for i in range(min(5, len(df))):
                row = df.iloc[i]
                print(f"    {i+1}: depth={row['depth']:.2f}m, temp={row['temperature']:.3f}C, sal={row['salinity']:.3f}, dens={row['density']:.3f}")
        
    except Exception as e:
        print(f"\n[ERROR] Cast {cast_num} ({cnv_file}): {str(e)[:80]}")

print(f"\n[OK] Successfully loaded {len(ctd_data)}/{len(cnv_files)} CTD profiles")

# Anomaly detection
if len(ctd_data) > 1:
    print("\n--- Anomaly Analysis ---")
    depths = [s['max_depth'] for s in ctd_stats.values()]
    temps_mean = [s['mean_temp'] for s in ctd_stats.values()]
    
    depth_avg = np.mean(depths)
    depth_std = np.std(depths)
    temp_avg = np.mean(temps_mean)
    
    issues = []
    for cast_id, stats in ctd_stats.items():
        if abs(stats['max_depth'] - depth_avg) > 2.5 * depth_std:
            issues.append(f"Cast {cast_id}: Depth {stats['max_depth']:.0f}m (avg {depth_avg:.0f}+/-{depth_std:.0f}m)")
        if abs(stats['mean_temp'] - temp_avg) > 2.5:
            issues.append(f"Cast {cast_id}: Temp {stats['mean_temp']:.1f}C (avg {temp_avg:.1f}C)")
    
    if issues:
        for issue in issues:
            print(f"  * {issue}")
    else:
        print("  [INFO] All casts within normal range")


# ============================================================================
# STEP 2: LOAD AND ANALYZE ADCP DATA
# ============================================================================
print("\n" + "="*80)
print("STEP 2: ADCP - ACOUSTIC DOPPLER CURRENT PROFILER DATA")
print("="*80)

adcp_data = None
adcp_info = {}
adcp_dir = "Raw data"

if os.path.isdir(adcp_dir):
    adcp_files = os.listdir(adcp_dir)
    print(f"\nFound {len(adcp_files)} ADCP files in '{adcp_dir}'")
    
    # Get unique datasets
    datasets = set()
    for f in adcp_files:
        match = re.match(r'(MAR538ADCP\d+)', f)
        if match:
            datasets.add(match.group(1))
    
    print(f"Identified {len(datasets)} ADCP transect datasets:")
    for ds in sorted(datasets):
        ds_files = [f for f in adcp_files if f.startswith(ds)]
        print(f"  {ds}: {len(ds_files)} files")
        for ext in set(f.split('.')[-1] for f in ds_files):
            ext_files = [f for f in ds_files if f.endswith(ext)]
            print(f"    .{ext}: {len(ext_files)} file(s)")
    
    # Try to load the test_all_mat_1.mat file if it exists
    mat_path = os.path.join("new processed", "test_all_mat_1.mat")
    if os.path.exists(mat_path):
        print(f"\n[OK] Located processed ADCP file: {mat_path}")
        try:
            adcp_data = scipy.io.loadmat(mat_path)
            
            print("\n--- Processed ADCP Variables ---")
            var_count = 0
            for var_name in sorted(adcp_data.keys()):
                if not var_name.startswith('__'):
                    var = adcp_data[var_name]
                    var_count += 1
                    shape = str(var.shape)
                    
                    # Get sample values - handle errors in min/max
                    try:
                        flat_var = var.flatten()
                        if len(flat_var) > 0:
                            var_min = float(np.min(flat_var))
                            var_max = float(np.max(flat_var))
                            var_mean = float(np.mean(flat_var))
                        else:
                            var_min = var_max = var_mean = None
                    except Exception as e:
                        var_min = var_max = var_mean = None
                    
                    adcp_info[var_name] = {
                        'shape': shape,
                        'type': str(var.dtype),
                        'size': var.size,
                        'min': var_min,
                        'max': var_max,
                        'mean': var_mean
                    }
                    
                    if var_min is not None and var_max is not None and var_mean is not None:
                        print(f"\n  {var_name}:")
                        print(f"    Shape: {shape}, Type: {var.dtype}")
                        print(f"    Min: {var_min:.4f}, Max: {var_max:.4f}, Mean: {var_mean:.4f}")
                    else:
                        print(f"\n  {var_name}:")
                        print(f"    Shape: {shape}, Type: {var.dtype}")
                        print(f"    [Could not compute statistics]")
            
            print(f"\n[OK] Loaded {var_count} variables from processed ADCP file")
            
            # Extract velocity components and calculate current speed
            print("\n--- Velocity Analysis ---")
            if 'AnNVEmmpersec' in adcp_data and 'AnNVNmmpersec' in adcp_data:
                try:
                    vel_e_raw = adcp_data['AnNVEmmpersec'].flatten().astype(float)
                    vel_n_raw = adcp_data['AnNVNmmpersec'].flatten().astype(float)
                    
                    # Convert mm/s to m/s
                    vel_e = vel_e_raw / 1000.0  # mm/s to m/s
                    vel_n = vel_n_raw / 1000.0  # mm/s to m/s
                    
                    # Calculate current speed
                    current_speed = np.sqrt(vel_e**2 + vel_n**2)
                    
                    # Calculate current direction (degrees from North, clockwise)
                    current_dir = np.arctan2(vel_e, vel_n) * 180.0 / np.pi
                    current_dir = (current_dir + 360) % 360  # Convert to 0-360 range
                    
                    print(f"\nEast-West Velocity (m/s):")
                    print(f"  Min: {vel_e.min():.4f}, Max: {vel_e.max():.4f}")
                    print(f"  Mean: {vel_e.mean():.4f}")
                    
                    print(f"\nNorth-South Velocity (m/s):")
                    print(f"  Min: {vel_n.min():.4f}, Max: {vel_n.max():.4f}")
                    print(f"  Mean: {vel_n.mean():.4f}")
                    
                    print(f"\nCurrent Speed (m/s):")
                    print(f"  Min: {current_speed.min():.4f} m/s")
                    print(f"  Max: {current_speed.max():.4f} m/s")
                    print(f"  Mean: {current_speed.mean():.4f} m/s")
                    
                    print(f"\nCurrent Direction (degrees from North):")
                    print(f"  Min: {current_dir.min():.1f}Â°")
                    print(f"  Max: {current_dir.max():.1f}Â°")
                    print(f"  Mean: {current_dir.mean():.1f}Â°")
                    print(f"  Range: {current_dir.max() - current_dir.min():.1f}Â°")
                except Exception as e:
                    print(f"  [ERROR] Calculating velocity: {e}")
            else:
                print("  Velocity variables not found!")
            
            # Identify variable types
            print("\n--- Variable Classification ---")
            vel_vars = [v for v in adcp_info.keys() if any(x in v.lower() for x in ['vel', 'u', 'v', 'w', 'speed'])]
            depth_vars = [v for v in adcp_info.keys() if any(x in v.lower() for x in ['depth', 'bin', 'z'])]
            time_vars = [v for v in adcp_info.keys() if any(x in v.lower() for x in ['time', 't'])]
            pos_vars = [v for v in adcp_info.keys() if any(x in v.lower() for x in ['lat', 'lon', 'x', 'y'])]
            
            print(f"  Velocity components: {vel_vars if vel_vars else 'None found'}")
            print(f"  Depth/bin variables: {depth_vars if depth_vars else 'None found'}")
            print(f"  Time variables: {time_vars if time_vars else 'None found'}")
            print(f"  Position variables: {pos_vars if pos_vars else 'None found'}")
            
        except Exception as e:
            print(f"[ERROR] Loading ADCP .mat file: {e}")
    else:
        print(f"[WARNING] ADCP .mat file not found at {mat_path}")

else:
    print(f"[WARNING] ADCP directory '{adcp_dir}' not found")


# ============================================================================
# STEP 3: LOAD AND ANALYZE SURFACE TRANSECT DATA
# ============================================================================
print("\n" + "="*80)
print("STEP 3: SURFACE TRANSECT - TEMPERATURE AND SALINITY WITH GPS")
print("="*80)

transect_ctd = None
transect_gps = None
event_log = ""
transect_combined = None

# Try to load surface transect .mat files directly from main directory
print("\n--- Looking for Surface Transect Files ---")
