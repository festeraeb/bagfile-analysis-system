# Resume pipeline helper (run locally) - created: 2026-02-02T11:48Z
# Usage: Open PowerShell in repo root and run: .\scripts\resume_pipeline.ps1

param()

Write-Host "=== CESAROPS Resume Helper ==="
Write-Host "1) Ensure conda/env is activated and required packages are installed: pyyaml, rasterio, rasterio deps"
Write-Host "   Example: pip install pyyaml rasterio"

function Pause-ForUser {
    Read-Host "Press Enter to continue to next step (Ctrl+C to abort)"
}

# Step 1: Finish S-102 extraction
Write-Host "Step 1: Extract remaining S-102 ExchangeSets (if any)"
Write-Host "Command: python scripts/extract_tifs_from_s102.py --src magnetic_data/s102_downloads --out magnetic_data/s102_samples"
Pause-ForUser
python scripts/extract_tifs_from_s102.py --src magnetic_data/s102_downloads --out magnetic_data/s102_samples

# Step 2: Rebuild EMAG/MBES coverage report
Write-Host "Step 2: Rebuild EMAG/MBES/trackline coverage report"
Pause-ForUser
python scripts/emag_mbes_trackline_coverage_report.py --targets predictions/merged_target_wrecks.csv

# Step 3: (Optional) Install rasterio and sample bathymetry to fill depth flags
Write-Host "Step 3: If you installed rasterio/pyyaml, re-run depth grouping to set priority targets"
Pause-ForUser
python scripts/group_wrecks_by_lake_and_prioritize.py --merged predictions/merged_target_wrecks.csv --outdir predictions

# Step 4: Run per-lake detectability / matched-filter for priority targets
Write-Host "Step 4: Suggested detectability run (example for 'michigan')"
Write-Host "Command example: python scripts/run_detectability_for_list.py --targets predictions/wrecks_michigan_* --out predictions/michigan_detectability.csv"
Pause-ForUser
# Replace with actual call you want, example placeholder:
# python scripts/run_detectability_for_list.py --targets predictions/wrecks_michigan_*.csv --out predictions/michigan_detectability.csv

# Step 5: Parametric detectability / retrain
Write-Host "Step 5: Run parametric experiments and retrain if desired"
Pause-ForUser
# python scripts/parametric_detectability.py --patch-dir predictions/patches --out training/parametric
# python scripts/assemble_and_train_sim_aug.py --config configs/train.yaml

# Step 6: Generate ingest manifest and resume Azure uploads
Write-Host "Step 6: Generate Azure ingest manifest and resume blob uploads (if desired)"
Pause-ForUser
python scripts/generate_azure_ingest_manifest.py --root magnetic_data --out predictions/azure_ingest_manifest.json
python scripts/azure_ingest_blob_table.py --manifest predictions/azure_ingest_manifest.json --upload

Write-Host "=== Resume helper finished. Check outputs under predictions/ and training/ ==="
