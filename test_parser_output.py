#!/usr/bin/env python3
"""Test parser output to understand bounds"""

from src.sonarsniffer.sonar_parser import SonarParser

p = SonarParser()
result = p.parse_file(r"HummSucker\Garmin-Rsd\SonarSniffer\samples\Holloway.RSD")
meta = result["metadata"]

print("Metadata:")
print(f'  Record count: {meta.get("record_count")}')
print(f'  Total in file: {meta.get("total_records_in_file")}')
print(f'  Bounds: {meta.get("bounds")}')

# Get actual min/max from records
records = result["records"]
lats = [r["lat"] for r in records if r["lat"] != 0.0]
lons = [r["lon"] for r in records if r["lon"] != 0.0]

print(f"\nActual data from records:")
print(f"  Valid lat/lon pairs: {len(lats)}")
if lats:
    print(f"  Latitude: {min(lats):.6f} to {max(lats):.6f}")
    print(f"  Longitude: {min(lons):.6f} to {max(lons):.6f}")

print(f"\nFirst 10 records:")
for i, r in enumerate(records[:10]):
    print(f'  {i}: lat={r["lat"]:.6f}, lon={r["lon"]:.6f}')

# Check if coordinates cluster around Flint area (43.125, -83.434)
print(f"\nLooking for Flint cluster (43.125, -83.434):")
flint_cluster = []
for r in records:
    if r["lat"] != 0.0 and r["lon"] != 0.0:
        if 43.0 <= r["lat"] <= 43.3 and -83.6 <= r["lon"] <= -83.2:
            flint_cluster.append(r)

print(f"  Records within 0.15° of Flint: {len(flint_cluster)}")
if flint_cluster:
    print(f"  First few:")
    for r in flint_cluster[:5]:
        print(f'    {r["lat"]:.6f}, {r["lon"]:.6f}')
