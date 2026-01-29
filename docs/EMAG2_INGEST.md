# EMAG2 Ingest Summary

This document summarizes the EMAG2 ingestion addition (branch: `magwork`).

What was added:
- `scripts/ingest_emag2.py` — download EMAG2 CSV zip from NCEI, subset to Great Lakes bbox, grid to GeoTIFF, and optionally tile into 256×256 numpy patches.
- `scripts/ensemble_predictions.py` — updated to resample probability rasters to a common grid before averaging.
- `scripts/submit_train_to_azure.py` — helper to estimate cost, upload `training/` to Azure Blob, and write an Azure ML job YAML. The script records estimated spend in `scripts/.spend_ledger.json` and will abort if the estimated job would exceed the current budget.
- `docs/next_steps.md` — quick instructions for next actions (Sentinel patches, recompute ensemble, Azure submit).

Notes:
- No large datasets or databases are committed. Please follow `docs/INGEST_DATA_POLICY.md` when adding new datasets.
- To test the EMAG2 ingestion locally run (after installing dependencies):
  - python scripts/ingest_emag2.py --download --out-dir magnetic_data/grids/emag2 --bbox -92.5 41 -75 49 --tile-patches

If you want, I can also open a PR from `magwork` and include this summary in the PR description.