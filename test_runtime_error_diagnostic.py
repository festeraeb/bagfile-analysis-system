#!/usr/bin/env python3
"""
Runtime Error API Diagnostic
"""

import requests
import json

RUNTIME_ERROR_API = "https://cesarops.com/api_runtime_error_IONOS.php"

print("\n" + "=" * 70)
print("Runtime Error API Detailed Diagnostic")
print("=" * 70)

test_error = {
    "error_type": "ValueError",
    "error_message": "TEST error",
    "platform": "win32",
    "sonar_version": "1.0.0",
    "feature_used": "test",
}

print(f"\nTest Data (minimal):")
for key, value in test_error.items():
    print(f"  {key}: {value}")

try:
    response = requests.post(RUNTIME_ERROR_API, json=test_error, timeout=10)

    print(f"\nResponse:")
    print(f"  Status Code: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('content-type', 'not specified')}")
    print(f"  Content Length: {len(response.text)} bytes")

    print(f"\nRaw Response (full):")
    if response.text:
        print(f"  {response.text[:500]}")
    else:
        print(f"  (empty response)")

except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "=" * 70)
