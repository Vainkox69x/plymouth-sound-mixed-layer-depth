Project: Plymouth Sound Hydrographic Analysis

This repository contains code and data used to analyse hydrographic observations from Plymouth Sound
collected on 11 March 2026. The analysis covers CTD profiles, ADCP current measurements, and derived
surface salinity products.

Contents
- data/: recommended location for raw and processed data files.
- scripts/: Python scripts used to process data and generate figures.
- outputs/: generated figures and summary tables (output files produced by the scripts).
- docs/: supporting documents and notes about the project.

Data sources
- CTD files (Sea-Bird CNV format): these are the profile files named like `20260311_CTD001_conv.cnv`.
- ADCP: MATLAB `.mat` files in `new processed/` used by the ADCP plotting scripts.
- Other auxiliary CSVs and MAT files included in the repository.

Methods
- CTD processing: CNV files are parsed after the `*END*` marker. Basic filtering removes rows with
  invalid salinity (e.g. salinity <= 0) and trims pre-water rows using simple salinity and depth tests.
- ADCP processing: MATLAB `.mat` files are loaded via `scipy.io.loadmat`; ensemble/bin data are
  converted to m/s and depth-averaged to create time series.
- Plots and summaries are generated with `matplotlib` and `pandas` for time handling.

How to run
1. Create and activate a Python 3.8+ virtual environment.

   python -m venv .venv
   .venv\\Scripts\\activate

2. Install dependencies:

   pip install -r requirements.txt

3. Run scripts from the repository root. Example commands:

   python ctd_analysis.py
   python adcp_current_speed_timeseries.py
   python verify_ctd_cnvs.py

4. Output files will be written to `outputs/` or `figures/` as described in each script.

Notes and recommendations
- The repository currently contains raw data directories (`Raw data/`, `CTD Raw data/`). For a
  cleaner upload to GitHub, move raw files to `data/raw/` and processed MAT/CSV files to `data/processed/`.
- Avoid committing large raw datasets to GitHub; consider using Git LFS for large files.
