#!/usr/bin/env python3
"""Prepare and optionally submit a training job to Azure ML.
- Uploads training data (if connection string provided)
- Estimates training cost and records estimated spend via ledger
- Writes an Azure ML job YAML to be submitted
- Attempts to call `az ml job create -f <yaml>` if az CLI is available
"""
import argparse
from pathlib import Path
import os
import subprocess
import sys

from scripts.spend_ledger import record_spend, get_total_spend, get_budget
from scripts.azure_cost_estimator import SKUS

TAR_DIR = Path('training')
YAML_OUT = Path('scripts/azure_train_job.yml')


def estimate_training_cost(hours, sku='t4'):
    cost_per_hour = SKUS[sku]['cost_per_hour']
    return hours * cost_per_hour


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--connection-string', default=os.environ.get('AZURE_STORAGE_CONNECTION_STRING'))
    p.add_argument('--container', default='shipwreck-analysis')
    p.add_argument('--sku', choices=list(SKUS.keys()), default='t4')
    p.add_argument('--hours', type=float, default=10.0, help='Estimated GPU hours for the full training')
    p.add_argument('--submit', action='store_true')
    args = p.parse_args()

    est_cost = estimate_training_cost(args.hours, sku=args.sku)
    total_spent = get_total_spend()
    budget = get_budget()
    print(f'Estimated training cost: ${est_cost:.2f}; spent so far: ${total_spent:.2f}; budget: ${budget:.2f}')

    if total_spent + est_cost >= budget:
        print('This training would exceed the budget. Aborting. Adjust hours or SKU or increase budget.')
        return

    # Record estimated spend
    record_spend(est_cost, f'Estimated training job cost ({args.sku}, {args.hours}h)')
    print('Recorded estimated spend to ledger')

    # Upload training tar if connection string provided
    if args.connection_string:
        print('Uploading training/ to Azure Blob...')
        cmd = [sys.executable, 'scripts/upload_to_azure_blob.py', '--connection-string', args.connection_string, '--container', args.container, '--paths', 'training', '--prefix', 'training_data', '--create-container']
        subprocess.check_call(cmd)
        print('Upload done. Please submit the following job YAML to Azure ML (adjust placeholders as needed):')
    else:
        print('No connection string provided — skipping upload. Please upload training data manually if needed.')

    # Write a simple job YAML (template)
    yaml = f"""$schema: https://azuremlschemas.azureedge.net/latest/commandJob.schema.json
$version: 1
code: .
command: >-
  python scripts/train_unet_full.py --data-dirs training/synthetic_mbess training/synthetic_mag training/ai4shipwrecks_patches --out training/models/unet_full.pt --epochs 50 --batch-size 16
environment:
  image: mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04
compute:
  target: gpu-cluster-1
resources:
  instance_count: 1
"""
    YAML_OUT.write_text(yaml)
    print('Wrote job YAML to', YAML_OUT)

    if args.submit:
        # try to submit with az ml if available
        try:
            subprocess.check_call(['az','ml','job','create','-f', str(YAML_OUT)])
            print('Submitted job via az ml')
        except Exception as e:
            print('Could not submit via az ml (not installed or error). Use the YAML file to submit manually.')

if __name__ == '__main__':
    main()
