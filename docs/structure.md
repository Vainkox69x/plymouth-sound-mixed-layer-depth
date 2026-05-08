Recommended project structure

- data/
  - raw/          # raw source data (do NOT commit large raw files to GitHub)
  - processed/    # processed MAT/CSV files used by scripts
- scripts/        # optional: utility scripts (many are currently at repository root)
- outputs/
  - figures/
  - tables/
- docs/           # notes, structure, and supporting docs

Notes
- To prepare the repo for GitHub, move large raw datasets out of the repo or use Git LFS.
- Update script file paths if you move data files; many scripts assume the repository root working directory.
