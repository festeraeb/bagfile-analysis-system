#!/usr/bin/env python3
"""Register a grid file into magnetic_data/inventory.csv"""
from pathlib import Path
import argparse
import csv
from datetime import datetime

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', required=True)
    p.add_argument('--source', default='USGS_NAmag')
    p.add_argument('--desc', default='North American Magnetic Anomaly Grid subset')
    args = p.parse_args()

    f = Path(args.file)
    if not f.exists():
        print('File not found:', f)
        return
    inv = Path('magnetic_data/inventory.csv')
    exists = inv.exists()
    with inv.open('a', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        if not exists:
            writer.writerow(['filename','source','description','size_bytes','created_utc'])
        writer.writerow([str(f), args.source, args.desc, str(f.stat().st_size), datetime.utcnow().isoformat()+'Z'])
    print('Registered', f, 'in inventory')

if __name__ == '__main__':
    main()
