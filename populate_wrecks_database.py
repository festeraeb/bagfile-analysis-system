import sqlite3
import json
from datetime import datetime

# Hardcoded priority targets from robust_bag_scanner.py
priority_targets = [
    {"name": "Elva Candidate 1 (PDF Confirmed)", "latitude": 45.849306, "longitude": -84.613028, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "Elva Candidate 2 (PDF Confirmed)", "latitude": 45.849194, "longitude": -84.612333, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "Cedarville Wreck (PDF)", "latitude": 45.808583, "longitude": -84.732444, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "PDF Wreck 1", "latitude": 45.812944, "longitude": -84.698167, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "PDF Wreck 2", "latitude": 45.793889, "longitude": -84.684333, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "PDF Wreck 3", "latitude": 45.788972, "longitude": -84.672194, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "PDF Wreck 4", "latitude": 45.700028, "longitude": -84.441333, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "PDF Wreck 5", "latitude": 45.838083, "longitude": -85.157139, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "PDF Wreck 6", "latitude": 45.789056, "longitude": -85.080250, "feature_type": "Wreck", "source": "robust_bag_scanner.py"},
    {"name": "Elva Area Obstruction 1", "latitude": 45.844111, "longitude": -84.618778, "feature_type": "Obstruction", "source": "robust_bag_scanner.py"},
    {"name": "Elva Area Obstruction 2", "latitude": 45.844250, "longitude": -84.618694, "feature_type": "Obstruction", "source": "robust_bag_scanner.py"},
    {"name": "Elva Area Obstruction 3", "latitude": 45.844167, "longitude": -84.618472, "feature_type": "Obstruction", "source": "robust_bag_scanner.py"},
    {"name": "Feature 1.2 (SHPO Hidden)", "latitude": 45.725361, "longitude": -84.422902, "feature_type": "Obstruction", "source": "robust_bag_scanner.py"},
    {"name": "Feature 1.4 (SHPO Hidden)", "latitude": 45.801472, "longitude": -84.623930, "feature_type": "Obstruction", "source": "robust_bag_scanner.py"}
]

# Real coordinates from real_coordinate_maritime_gallery.py (fallback)
real_coordinates = {
    "H13253_1.11": {"lat": 45.789056, "lon": -85.080250, "depth": "3.24m", "feature": "Wreck", "description": "Primary wreck site", "chart": "14881"},
    "H13253_1.14": {"lat": 45.794528, "lon": -85.071989, "depth": "7.69m", "feature": "Obstruction", "description": "Primary obstruction", "chart": "14881"},
    "H13253_1.17": {"lat": 45.794972, "lon": -85.068194, "depth": "8.36m", "feature": "Obstruction", "description": "Secondary obstruction", "chart": "14881"},
    "W00555_1.1": {"lat": 45.056389, "lon": -83.426306, "depth": "2.57m", "feature": "Obstruction", "description": "Thunder Bay obstruction", "chart": "14864"}
}

def insert_features(cursor, features):
    for f in features:
        cursor.execute("""
            INSERT INTO features (name, latitude, longitude, depth, feature_type, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f.get("name"),
            f.get("latitude"),
            f.get("longitude"),
            f.get("depth"),
            f.get("feature_type"),
            f.get("source")
        ))

def main():
    conn = sqlite3.connect('wrecks.db')
    cursor = conn.cursor()
    with open('wrecks_database_schema.sql', 'r') as f:
        cursor.executescript(f.read())
    # Insert priority targets
    insert_features(cursor, priority_targets)
    # Insert real coordinates
    for key, rc in real_coordinates.items():
        cursor.execute("""
            INSERT INTO features (name, latitude, longitude, depth, feature_type, source, historical_place_names)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            key,
            rc.get("lat"),
            rc.get("lon"),
            rc.get("depth"),
            rc.get("feature"),
            "real_coordinate_maritime_gallery.py",
            rc.get("description")
        ))
    conn.commit()
    conn.close()
    print("Database wrecks.db populated with initial features.")

if __name__ == "__main__":
    main()
