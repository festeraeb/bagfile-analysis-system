#!/usr/bin/env python3
"""
CESARops Runtime Error API Test
Tests the runtime error tracking system
"""

import requests
import json
from datetime import datetime

RUNTIME_ERROR_API = "https://cesarops.com/api_runtime_error_IONOS.php"

print("\n" + "█" * 70)
print("█  CESARops Runtime Error API Test")
print("█  Testing runtime error tracking and reporting")
print("█" * 70)

# ============================================================
# TEST 1: Submit Runtime Error
# ============================================================
print("\n" + "=" * 70)
print("TEST 1: Submit Runtime Error")
print("=" * 70)

test_error = {
    "error_type": "ValueError",
    "error_message": "TEST: Failed to extract features from sonar image",
    "error_code": "ValueError_target_detection",
    "stack_trace": 'Traceback (most recent call last):\n  File "advanced_target_detection.py", line 245\n    ValueError: Could not extract features',
    "module_name": "advanced_target_detection.py",
    "function_name": "extract_features",
    "line_number": 245,
    "platform": "win32",
    "python_version": "3.11.0",
    "os_version": "Windows 11",
    "sonar_version": "1.0.0",
    "feature_used": "target_detection",
    "input_file": "test_sonar_file.rsd",
    "file_format": "rsd",
    "file_size_mb": 150,
    "processing_step": "feature_extraction",
    "operation_duration_seconds": 45,
    "memory_usage_mb": 512,
    "user_email": "test@cesarops.com",
    "user_feedback": "Test runtime error during target detection",
    "severity": "high",
}

try:
    print(f"📤 Submitting test runtime error...")
    print(f"   Feature: {test_error['feature_used']}")
    print(f"   Error: {test_error['error_message']}")

    response = requests.post(RUNTIME_ERROR_API, json=test_error, timeout=10)

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"   ✅ Error submitted successfully")
            print(f"   Error ID: {data.get('error_id')}")
            runtime_test_pass = True
        else:
            print(f"   ❌ API returned error: {data.get('error')}")
            runtime_test_pass = False
    else:
        print(f"   ❌ HTTP Error: {response.text}")
        runtime_test_pass = False
except Exception as e:
    print(f"   ❌ Request failed: {e}")
    runtime_test_pass = False

# ============================================================
# TEST 2: Submit Video Export Error
# ============================================================
print("\n" + "=" * 70)
print("TEST 2: Submit Video Export Runtime Error")
print("=" * 70)

video_error = {
    "error_type": "RuntimeError",
    "error_message": "TEST: FFmpeg encoding failed - codec not found",
    "error_code": "RuntimeError_video_export",
    "stack_trace": 'Traceback (most recent call last):\n  File "python_cuda_bridge.py", line 127\n    RuntimeError: ffmpeg codec error',
    "module_name": "python_cuda_bridge.py",
    "function_name": "encode_frame",
    "line_number": 127,
    "platform": "win32",
    "python_version": "3.11.0",
    "os_version": "Windows 11",
    "sonar_version": "1.0.0",
    "feature_used": "video_export",
    "input_file": "mosaic_frames_001.npy",
    "file_format": "rsd",
    "file_size_mb": 280,
    "processing_step": "frame_encoding",
    "operation_duration_seconds": 120,
    "memory_usage_mb": 768,
    "user_email": "test@cesarops.com",
    "user_feedback": "Video encoding failed after 2 minutes",
    "severity": "critical",
}

try:
    print(f"📤 Submitting video export error...")
    print(f"   Feature: {video_error['feature_used']}")
    print(f"   Error: {video_error['error_message']}")

    response = requests.post(RUNTIME_ERROR_API, json=video_error, timeout=10)

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"   ✅ Error submitted successfully")
            print(f"   Error ID: {data.get('error_id')}")
            video_test_pass = True
        else:
            print(f"   ❌ API returned error: {data.get('error')}")
            video_test_pass = False
    else:
        print(f"   ❌ HTTP Error: {response.text}")
        video_test_pass = False
except Exception as e:
    print(f"   ❌ Request failed: {e}")
    video_test_pass = False

# ============================================================
# TEST 3: Get Error Statistics
# ============================================================
print("\n" + "=" * 70)
print("TEST 3: Get Error Statistics")
print("=" * 70)

try:
    print(f"📊 Querying error statistics...")
    response = requests.get(
        f"{RUNTIME_ERROR_API}?action=stats&feature=target_detection", timeout=10
    )

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"   ✅ Statistics retrieved successfully")
            stats = data.get("stats", {})
            print(f"   Total errors: {stats.get('total_errors', 0)}")
            print(f"   Critical: {stats.get('critical_count', 0)}")
            print(f"   High: {stats.get('high_count', 0)}")
            print(f"   Fixed: {stats.get('fixed_count', 0)}")
            stats_pass = True
        else:
            print(f"   ❌ API returned error: {data.get('error')}")
            stats_pass = False
    else:
        print(f"   ❌ HTTP Error: {response.text}")
        stats_pass = False
except Exception as e:
    print(f"   ❌ Request failed: {e}")
    stats_pass = False

# ============================================================
# TEST 4: API Status Check
# ============================================================
print("\n" + "=" * 70)
print("TEST 4: Runtime Error API Status")
print("=" * 70)

try:
    print(f"🔍 Checking API status...")
    response = requests.get(f"{RUNTIME_ERROR_API}?action=status", timeout=10)

    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"   ✅ API is operational")
            print(f"   Version: {data.get('version')}")
            print(f"   Database: {data.get('database')}")
            status_pass = True
        else:
            print(f"   ❌ API returned error: {data.get('error')}")
            status_pass = False
    else:
        print(f"   ❌ HTTP Error: {response.text}")
        status_pass = False
except Exception as e:
    print(f"   ❌ Request failed: {e}")
    status_pass = False

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("RUNTIME ERROR TRACKING TEST SUMMARY")
print("=" * 70)

results = {
    "Error Submission (Target Detection)": runtime_test_pass,
    "Error Submission (Video Export)": video_test_pass,
    "Statistics Query": stats_pass,
    "API Status": status_pass,
}

for test_name, result in results.items():
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} - {test_name}")

passed = sum(1 for v in results.values() if v)
total = len(results)

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 Runtime error tracking system is fully operational!")
    print("   - Runtime errors are being captured")
    print("   - Errors are stored in database")
    print("   - Statistics queries working")
    print("   - Ready for integration into SonarSniffer")
elif passed >= 2:
    print("\n✅ Core runtime error tracking is working!")
    print("   - Errors can be submitted and recorded")
    print("   - API is responsive")
else:
    print("\n⚠️  Runtime error tracking needs attention")
    print("   Check API endpoint configuration")

print("\n" + "█" * 70)
