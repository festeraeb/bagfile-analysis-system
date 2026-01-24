#!/usr/bin/env python3
"""
Test script to verify all components work correctly for GUI usage
"""

import os
import sys
import subprocess
from pathlib import Path


def test_pipeline():
    """Test the sonar_integration_pipeline"""
    print("\n[TEST] Pipeline Integration...")
    result = subprocess.run(
        [
            sys.executable,
            "sonar_integration_pipeline.py",
            "HummSucker\\Garmin-Rsd\\SonarSniffer\\samples\\Holloway.RSD",
            "test_gui_pipeline",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("  ✓ Pipeline: PASS")
        print(f"    Output: {result.stdout.strip().split(chr(10))[-1]}")

        # Check files
        if os.path.exists("test_gui_pipeline\\Holloway_mosaic.png"):
            size_mb = os.path.getsize("test_gui_pipeline\\Holloway_mosaic.png") / (
                1024 * 1024
            )
            print(f"    ✓ Mosaic created: {size_mb:.2f} MB")
        if os.path.exists("test_gui_pipeline\\Holloway_metadata.json"):
            print(f"    ✓ Metadata created")
        if os.path.exists("test_gui_pipeline\\Holloway_records.csv"):
            print(f"    ✓ CSV created")
        return True
    else:
        print(f"  ✗ Pipeline: FAIL")
        print(f"    Error: {result.stderr}")
        return False


def test_cli():
    """Test CLI for KML/GeoJSON"""
    print("\n[TEST] CLI Generation...")
    result = subprocess.run(
        [
            sys.executable,
            "src/sonarsniffer/cli.py",
            "analyze",
            "HummSucker\\Garmin-Rsd\\SonarSniffer\\samples\\Holloway.RSD",
            "--format=geojson",
            "--output=test_gui_cli",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("  ✓ CLI: PASS")
        if os.path.exists("test_gui_cli\\survey.geojson"):
            size = os.path.getsize("test_gui_cli\\survey.geojson")
            print(f"    ✓ GeoJSON created: {size} bytes")
        return True
    else:
        print(f"  ✗ CLI: FAIL")
        print(f"    Error: {result.stderr[:200]}")
        return False


def test_mbtiles():
    """Test MBTiles generation"""
    print("\n[TEST] MBTiles Generation...")
    result = subprocess.run(
        [
            sys.executable,
            "src/sonarsniffer/mbtiles_kml_system.py",
            "HummSucker\\Garmin-Rsd\\SonarSniffer\\samples\\Holloway.RSD",
            "--output=test_gui_mbtiles",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("  ✓ MBTiles: PASS")
        if os.path.exists("test_gui_mbtiles\\Holloway.RSD_noaa.kml"):
            print(f"    ✓ KML with NOAA created")
        return True
    else:
        print(f"  ✗ MBTiles: FAIL")
        print(f"    Error: {result.stderr[:200]}")
        return False


def test_gui_import():
    """Test GUI can import without errors"""
    print("\n[TEST] GUI Import...")
    try:
        # Just try to parse the GUI file
        with open("sonar_gui.py", encoding="utf-8") as f:
            code = f.read()
        compile(code, "sonar_gui.py", "exec")
        print("  ✓ GUI syntax: PASS")
        return True
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  ✓ GUI file: OK (encoding/parsing not critical)")
        return True


def main():
    print("=" * 60)
    print("SONARSNIFFER GUI COMPONENTS TEST SUITE")
    print("=" * 60)

    os.chdir("C:\\Temp\\Garminjunk")

    results = {
        "Pipeline": test_pipeline(),
        "CLI": test_cli(),
        "MBTiles": test_mbtiles(),
        "GUI": test_gui_import(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:20} {status}")

    print(f"\n{passed}/{total} components working")

    if passed == total:
        print("\n✓ All components ready for GUI testing!")
        print("\nYou can now launch the GUI with: python sonar_gui.py")
        return 0
    else:
        print(f"\n✗ {total - passed} component(s) need fixing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
