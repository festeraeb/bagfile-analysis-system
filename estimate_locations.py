import sqlite3
import json
import re

import sqlite3
import json
import re

# Location estimation based on historical place names and known wreck data
LOCATION_ESTIMATES = {
    # Michigan ports and landmarks
    "mackinac": {"lat": 45.8492, "lon": -84.6192, "name": "Mackinac Island"},
    "mackinaw city": {"lat": 45.7770, "lon": -84.7275, "name": "Mackinaw City"},
    "st. ignace": {"lat": 45.8664, "lon": -84.7277, "name": "St. Ignace"},
    "cheboygan": {"lat": 45.6469, "lon": -84.4744, "name": "Cheboygan"},
    "petoskey": {"lat": 45.3736, "lon": -84.9553, "name": "Petoskey"},
    "charlevoix": {"lat": 45.3186, "lon": -85.2597, "name": "Charlevoix"},
    "manistee": {"lat": 44.2444, "lon": -86.3242, "name": "Manistee"},
    "frankfort": {"lat": 44.6336, "lon": -86.2500, "name": "Frankfort"},
    "sleeping bear": {"lat": 44.7667, "lon": -86.0667, "name": "Sleeping Bear Dunes"},
    "south haven": {"lat": 42.4031, "lon": -86.2736, "name": "South Haven"},
    "holland": {"lat": 42.7875, "lon": -86.1089, "name": "Holland"},
    "grand haven": {"lat": 43.0631, "lon": -86.2284, "name": "Grand Haven"},
    "ludington": {"lat": 43.9553, "lon": -86.4526, "name": "Ludington"},
    "port huron": {"lat": 42.9708, "lon": -82.4249, "name": "Port Huron"},
    "alpena": {"lat": 45.0617, "lon": -83.4328, "name": "Alpena"},
    "tawas": {"lat": 44.2658, "lon": -83.4497, "name": "Tawas City"},
    "detroit": {"lat": 42.3314, "lon": -83.0458, "name": "Detroit"},
    "toledo": {"lat": 41.6528, "lon": -83.5379, "name": "Toledo"},
    "cleveland": {"lat": 41.4993, "lon": -81.6944, "name": "Cleveland"},
    "buffalo": {"lat": 42.8864, "lon": -78.8784, "name": "Buffalo"},
    "erie": {"lat": 42.1292, "lon": -80.0851, "name": "Erie"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "name": "Chicago"},
    "milwaukee": {"lat": 43.0389, "lon": -87.9065, "name": "Milwaukee"},
    "green bay": {"lat": 44.5192, "lon": -88.0198, "name": "Green Bay"},

    # Lake regions
    "lake huron": {"lat": 45.0, "lon": -83.0, "name": "Lake Huron"},
    "lake michigan": {"lat": 44.0, "lon": -87.0, "name": "Lake Michigan"},
    "lake superior": {"lat": 47.0, "lon": -88.0, "name": "Lake Superior"},
    "lake erie": {"lat": 42.0, "lon": -81.0, "name": "Lake Erie"},
    "lake ontario": {"lat": 43.5, "lon": -77.5, "name": "Lake Ontario"},
    "straits of mackinac": {"lat": 45.8, "lon": -84.7, "name": "Straits of Mackinac"},
    "thunder bay": {"lat": 45.0, "lon": -83.5, "name": "Thunder Bay"},
    "saginaw bay": {"lat": 43.8, "lon": -83.8, "name": "Saginaw Bay"},
    "grand traverse bay": {"lat": 45.0, "lon": -85.5, "name": "Grand Traverse Bay"},
    "little traverse bay": {"lat": 45.1, "lon": -85.3, "name": "Little Traverse Bay"},
    "detroit river": {"lat": 42.3, "lon": -83.1, "name": "Detroit River"},
    "st. clair river": {"lat": 42.5, "lon": -82.5, "name": "St. Clair River"},
    "apostle islands": {"lat": 46.9667, "lon": -90.6667, "name": "Apostle Islands"},

    # Specific Swayze locations
    "sand island": {"lat": 46.8667, "lon": -90.1667, "name": "Sand Island, Apostle Islands"},
    "bois blanc island": {"lat": 45.8000, "lon": -84.5167, "name": "Bois Blanc Island"},
    "west sister island": {"lat": 41.8167, "lon": -82.9667, "name": "West Sister Island"},
    "st. joseph": {"lat": 42.1097, "lon": -86.4800, "name": "St. Joseph"},
    "moraviantown": {"lat": 42.8333, "lon": -81.6667, "name": "Moraviantown, Ontario"},
    "thames river": {"lat": 42.7000, "lon": -81.5000, "name": "Thames River"},
    "port clinton": {"lat": 41.5120, "lon": -82.9377, "name": "Port Clinton"},
    "amherstburg": {"lat": 42.1000, "lon": -83.0833, "name": "Amherstburg, Ontario"},
    "chatham": {"lat": 42.4072, "lon": -82.1860, "name": "Chatham, Ontario"},
}

def estimate_location_from_place_name(place_name):
    """Estimate coordinates from place name"""
    if not place_name:
        return None, None

    place_lower = place_name.lower()

    # Direct matches
    for key, loc in LOCATION_ESTIMATES.items():
        if key in place_lower:
            return loc["lat"], loc["lon"]

    # Pattern matching for common locations
    if "mackinac" in place_lower:
        return 45.8, -84.7
    elif "huron" in place_lower:
        return 45.0, -83.0
    elif "michigan" in place_lower:
        return 44.0, -87.0
    elif "superior" in place_lower:
        return 47.0, -88.0
    elif "erie" in place_lower:
        return 42.0, -81.0
    elif "ontario" in place_lower:
        return 43.5, -77.5

    return None, None

def estimate_location_from_description(description, wreck_name):
    """Estimate location from description and wreck name"""
    if not description:
        description = ""
    if not wreck_name:
        wreck_name = ""

    combined_text = (description + " " + wreck_name).lower()

    # Specific Swayze location patterns
    if "sand isl" in combined_text or "sand island" in combined_text:
        return 46.8667, -90.1667
    elif "bois blanc" in combined_text:
        return 45.8000, -84.5167
    elif "west sister isl" in combined_text or "w sister isl" in combined_text:
        return 41.8167, -82.9667
    elif "st. joseph" in combined_text:
        return 42.1097, -86.4800
    elif "moraviantown" in combined_text:
        return 42.8333, -81.6667
    elif "thames r" in combined_text or "thames river" in combined_text:
        return 42.7000, -81.5000
    elif "port clinton" in combined_text:
        return 41.5120, -82.9377
    elif "amherstburg" in combined_text:
        return 42.1000, -83.0833
    elif "chatham" in combined_text:
        return 42.4072, -82.1860
    elif "apostles" in combined_text or "apostle islands" in combined_text:
        return 46.9667, -90.6667

    # Lake-specific patterns
    if "superior" in combined_text:
        return 47.0, -88.0
    elif "huron" in combined_text:
        return 45.0, -83.0
    elif "michigan" in combined_text:
        return 44.0, -87.0
    elif "erie" in combined_text:
        return 42.0, -81.0
    elif "ontario" in combined_text:
        return 43.5, -77.5
    elif "st. clair" in combined_text or "st clair" in combined_text:
        return 42.5, -82.5
    elif "detroit r" in combined_text or "detroit river" in combined_text:
        return 42.3, -83.1

    # General location patterns
    if "mackinac" in combined_text or "mackinaw" in combined_text:
        return 45.8, -84.7
    elif "thunder bay" in combined_text:
        return 45.0, -83.5
    elif "saginaw" in combined_text:
        return 43.8, -83.8
    elif "green bay" in combined_text:
        return 45.0, -87.5
    elif "manistee" in combined_text:
        return 44.2444, -86.3242
    elif "frankfort" in combined_text:
        return 44.6336, -86.2500
    elif "sleeping bear" in combined_text:
        return 44.7667, -86.0667
    elif "cheboygan" in combined_text:
        return 45.6469, -84.4744
    elif "petoskey" in combined_text:
        return 45.3736, -84.9553
    elif "charlevoix" in combined_text:
        return 45.3186, -85.2597
    elif "alpena" in combined_text:
        return 45.0617, -83.4328
    elif "tawas" in combined_text:
        return 44.2658, -83.4497
    elif "port huron" in combined_text:
        return 42.9708, -82.4249
    elif "ludington" in combined_text:
        return 43.9553, -86.4526
    elif "grand haven" in combined_text:
        return 43.0631, -86.2284
    elif "holland" in combined_text:
        return 42.7875, -86.1089
    elif "south haven" in combined_text:
        return 42.4031, -86.2736
    elif "st. ignace" in combined_text:
        return 45.8664, -84.7277
    elif "straits of mackinac" in combined_text:
        return 45.8, -84.7

    return None, None

def main():
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()

    # Get wrecks without coordinates, prioritizing Swayze data
    cursor.execute("""
        SELECT id, name, historical_place_names, feature_type, source
        FROM features
        WHERE (latitude IS NULL OR longitude IS NULL)
        AND name IS NOT NULL
        ORDER BY CASE WHEN source LIKE '%swayze%' THEN 1 ELSE 2 END
        LIMIT 2000  -- Process more records
    """)

    wrecks = cursor.fetchall()
    print(f"Processing {len(wrecks)} wrecks for location estimation...")

    swayze_count = sum(1 for w in wrecks if w[4] and 'swayze' in w[4].lower())
    print(f"Swayze records in batch: {swayze_count}")

    updated_count = 0
    for wreck_id, name, place_names, feature_type, source in wrecks:
        lat, lon = None, None

        # Try place name first
        if place_names:
            lat, lon = estimate_location_from_place_name(place_names)

        # Try description/name patterns (this now combines name and any description)
        if not lat and name:
            lat, lon = estimate_location_from_description("", name)

        # Try feature type hints
        if not lat and feature_type:
            if "huron" in feature_type.lower():
                lat, lon = 45.0, -83.0
            elif "michigan" in feature_type.lower():
                lat, lon = 44.0, -87.0

        if lat and lon:
            cursor.execute("""
                UPDATE features
                SET latitude = ?, longitude = ?
                WHERE id = ?
            """, (lat, lon, wreck_id))
            updated_count += 1
            source_indicator = " (Swayze)" if source and 'swayze' in source.lower() else ""
            print(f"Updated {name}{source_indicator}: {lat:.4f}, {lon:.4f}")

    conn.commit()
    conn.close()

    print(f"Location estimation complete! Updated {updated_count} wrecks.")

if __name__ == "__main__":
    main()