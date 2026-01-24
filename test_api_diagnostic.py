#!/usr/bin/env python3
"""
Detailed CESARops API Diagnostic Test
"""

import requests
import json

API_URLS = {
    "Install Tracker": "https://cesarops.com/api_install_tracker_IONOS.php",
    "Survey": "https://cesarops.com/api_submit_survey_IONOS.php",
}

print("\n" + "=" * 70)
print("CESARops API Diagnostic Test")
print("=" * 70)

for name, url in API_URLS.items():
    print(f"\n📡 Testing: {name}")
    print(f"   URL: {url}")

    try:
        # Test 1: Simple GET request
        print("   Attempting GET request...")
        response = requests.get(url, timeout=10)

        print(f"   Status Code: {response.status_code}")
        print(
            f"   Content-Type: {response.headers.get('content-type', 'not specified')}"
        )
        print(f"   Response Length: {len(response.text)} bytes")

        if response.text:
            print(f"   Raw Response (first 200 chars):")
            print(f"   {response.text[:200]}")

            # Try to parse as JSON
            try:
                data = response.json()
                print(f"   ✅ Valid JSON response")
                print(f"   JSON keys: {list(data.keys())}")
            except json.JSONDecodeError as e:
                print(f"   ❌ Not valid JSON: {e}")
        else:
            print(f"   ❌ Empty response")

    except Exception as e:
        print(f"   ❌ Request failed: {e}")

print("\n" + "=" * 70)
print("Website Accessibility Check")
print("=" * 70)

try:
    response = requests.get("https://cesarops.com/", timeout=10)
    print(f"✅ Website is accessible (status {response.status_code})")
except Exception as e:
    print(f"❌ Website not accessible: {e}")

print("\n" + "=" * 70)
