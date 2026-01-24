#!/usr/bin/env python3
"""Test the nextgen parser"""

from src.sonarsniffer.sonar_parser import SonarParser

p = SonarParser()
r = p.parse_file(r"HummSucker\Garmin-Rsd\SonarSniffer\samples\Holloway.RSD")
m = r["metadata"]

print(f"Records: {m.get('record_count')}")
print(f"Total in file: {m.get('total_records_in_file')}")
print(f"Bounds: {m.get('bounds')}")

# Show sample records
recs = r["records"][:5]
for rec in recs:
    print(f"  {rec['lat']:.6f}, {rec['lon']:.6f}")
