# Ingest Data Policy

Quick rules to avoid committing datasets, grids, or databases to the repository:

- **Never** commit raw or derived data files (e.g., `.tif`, `.npz`, `.zip`, `.db`, `.sqlite`, `.bag`, `.pdf`). Keep these out of Git history.
- Use the `magnetic_data/` and `training/` directories locally — but add them to `.gitignore` and do not commit their contents.
- Use `scripts/upload_to_azure_blob.py` to share artifacts to Blob Storage when needed; record storage estimates with `scripts/spend_ledger.py`.
- Keep a compact metadata CSV (no binary blobs) such as `magnetic_data/inventory.csv` to describe local data holdings (file names, source, acquisition date, footprint).
- If you need to add small sample files for tests (<1 MB), create `tests/data/` and add an explicit README explaining the file provenance and size.

If you want me to add automation to verify no large files are staged (pre-commit hook), I can add a `pre-commit` config that blocks large files from committing.