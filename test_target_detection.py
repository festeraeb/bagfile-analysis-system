#!/usr/bin/env python3
"""Test target detection with actual RSD file"""

import sys
import os
import numpy as np
import traceback
from src.sonarsniffer.advanced_target_detection import AdvancedTargetDetector
from src.sonarsniffer.sonar_parser import SonarParser

# Parse RSD file
print("Parsing RSD file...")
parser = SonarParser()
result = parser.parse_file(r"HummSucker\Garmin-Rsd\SonarSniffer\samples\Holloway.RSD")
records = result["records"]
print(f"  Parsed {len(records)} records")

# Try target detection
print("\nRunning target detection...")
detector = AdvancedTargetDetector()

success_count = 0
error_count = 0
targets_found_total = 0

try:
    for i, rec in enumerate(records[:100]):  # Test first 100
        if rec.get("sonar_size", 0) > 0:  # Has sonar data
            try:
                # Generate synthetic sonar data for testing
                # (In real use, this would come from the binary file)
                synthetic_sonar = np.random.rand(100, 100).astype(np.float32) * 0.3
                # Add some random "targets" (high intensity regions)
                for _ in range(np.random.randint(1, 4)):
                    y, x = np.random.randint(10, 90, 2)
                    synthetic_sonar[y : y + 10, x : x + 10] += (
                        np.random.rand(10, 10) * 0.7
                    )

                # Call detect_targets with synthetic sonar data
                targets = detector.detect_targets(sonar_data=synthetic_sonar)

                if targets:
                    targets_found_total += len(targets)
                    success_count += 1
                    if i < 5:
                        print(f"  Record {i}: Found {len(targets)} targets")
                else:
                    success_count += 1

            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    print(f"  Error in record {i}: {e}")
                    traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"Testing Complete:")
    print(f"  [OK] Successfully processed: {success_count}")
    print(f"  [FAIL] Errors: {error_count}")
    print(f"  [TARGETS] Total targets detected: {targets_found_total}")

except Exception as e:
    print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()

    traceback.print_exc()
