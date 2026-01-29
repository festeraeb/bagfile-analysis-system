# Next Steps (High Priority) ✅

This file summarizes the immediate actions to finish the remaining tasks you asked for: run the satellite (Sentinel-2) integration, standardize and recompute the ensemble, and submit a full training job to Azure (guarded by the local spend ledger).

## 1) Fetch Sentinel-2 patches for known wrecks (optional credentials)
- Ensure you have `pystac-client`, `planetary-computer`, and `rasterio` installed:
  - pip install pystac-client planetary-computer rasterio
- Run:
  - python scripts/sentinel_fetch_and_preprocess.py
- Output:
  - `training/sentinel_patches/{wreck_id}_{date}.npy` (channels: B04,B03,B02,NDWI proxy)

## 2) Recompute ensemble probability raster (fixed resampling) ⚙️
- Run the ensemble aggregation (now resamples to the first raster's grid):
  - python scripts/ensemble_predictions.py
- Convert to detections:
  - python scripts/prob_to_detections.py predictions/ensemble_prob.tif --threshold 0.5 --min_pixels 8
- Outputs:
  - `predictions/ensemble_prob.tif`
  - `predictions/ensemble_prob_detections.{geojson,csv,kml,html}`

## 3) Submit full training to Azure (budget-guarded) ☁️
- Prepare Azure storage connection string in `AZURE_STORAGE_CONNECTION_STRING` or pass `--connection-string`.
- Estimate GPU hours and cost with `--hours` and `--sku` (defaults: 10h, t4).
- Run dry-run first to print the estimate and see ledger status:
  - python scripts/submit_train_to_azure.py --hours 10 --sku t4
- To upload and record estimated spend (will abort if over budget):
  - python scripts/submit_train_to_azure.py --connection-string "<connstr>" --submit --hours 30 --sku v100
- The script writes `scripts/azure_train_job.yml` (edit if you need different commands or compute target) and attempts `az ml job create -f` if `az` is installed.

## Notes & Safety
- The local spend ledger is at `scripts/.spend_ledger.json` and defaults to a $25 budget. Edit with `scripts/spend_ledger.py` helpers.
- If you want me to submit the job now, tell me which `--sku` and expected `--hours` to use and confirm using Azure under the active budget.

---
Questions? Tell me which of the above you want me to run now: (A) fetch Sentinel patches, (B) submit the full Azure training job (give hours/sku), (C) recompute ensemble and extract detections. I can do any or all (with budget guard for Azure uploads/submissions).