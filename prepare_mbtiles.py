import sqlite3
import json
from datetime import datetime

def export_to_geojson():
    """Export database to GeoJSON format for MBTiles creation"""
    conn = sqlite3.connect('wrecks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all features with coordinates
    cursor.execute("""
        SELECT id, name, date, latitude, longitude, depth, feature_type, source, historical_place_names, newspaper_clip
        FROM features
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY name
    """)

    features = cursor.fetchall()
    conn.close()

    print(f"Exporting {len(features)} features to GeoJSON...")

    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for feature in features:
        feature_dict = dict(feature)

        # Create GeoJSON feature
        geojson_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [feature_dict['longitude'], feature_dict['latitude']]
            },
            "properties": {
                "id": feature_dict['id'],
                "name": feature_dict['name'] or f"Feature {feature_dict['id']}",
                "date": feature_dict['date'] or 'Unknown',
                "depth": feature_dict['depth'] or 'Unknown',
                "feature_type": feature_dict['feature_type'] or 'Unknown',
                "source": feature_dict['source'] or 'Unknown',
                "historical_place_names": feature_dict['historical_place_names'] or 'Unknown',
                "newspaper_clip": feature_dict['newspaper_clip'] or 'None',
                "coordinate_status": "estimated" if 'estimated' in str(feature_dict['source']).lower() else "verified"
            }
        }

        geojson["features"].append(geojson_feature)

    # Save GeoJSON file
    geojson_filename = f"wreck_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
    with open(geojson_filename, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)

    print(f"GeoJSON file saved as: {geojson_filename}")
    print("\nTo create MBTiles from this GeoJSON:")
    print("1. Install Tippecanoe: https://github.com/mapbox/tippecanoe")
    print(f"2. Run: tippecanoe -o wreck_database.mbtiles -l wrecks {geojson_filename}")
    print("3. The resulting .mbtiles file can be used in mapping applications")

    return geojson_filename

def create_mbtiles_readme():
    """Create README with MBTiles creation instructions"""
    readme_content = """
# Wreck Database MBTiles Creation

This directory contains the wreck database exported for MBTiles creation.

## Files
- `wreck_database_*.geojson` - GeoJSON export of wreck locations
- `wreck_database_*.kml` - KML export for Google Earth
- `newspaper_clips/` - Directory containing newspaper validation clips

## Creating MBTiles

### Option 1: Using Tippecanoe (Recommended)
1. Install Tippecanoe: https://github.com/mapbox/tippecanoe
2. Run the following command:
   ```
   tippecanoe -o wreck_database.mbtiles -l wrecks wreck_database_*.geojson
   ```

### Option 2: Using Mapbox Studio
1. Upload the GeoJSON file to Mapbox Studio
2. Create a new tileset
3. Export as MBTiles

## Using MBTiles

MBTiles files can be used in:
- Mapbox GL JS applications
- Mobile mapping apps
- Offline mapping solutions
- GIS software (QGIS, ArcGIS)

## Data Schema

Each feature contains:
- `name`: Wreck/feature name
- `date`: Loss/incident date
- `depth`: Water depth
- `feature_type`: Type of feature (wreck, obstruction, etc.)
- `source`: Data source
- `historical_place_names`: Associated locations
- `newspaper_clip`: Path to validation clip
- `coordinate_status`: "verified" or "estimated"

## Coordinate Status
- **verified**: Coordinates from official sources or direct measurement
- **estimated**: Coordinates estimated from place names and historical data
"""

    with open('MBTiles_README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("Created MBTiles_README.md with usage instructions")

def main():
    geojson_file = export_to_geojson()
    create_mbtiles_readme()

    print("\nReady for KML/MBTiles processing!")
    print(f"GeoJSON: {geojson_file}")
    print("KML: Run export_to_kml.py")
    print("MBTiles: Follow instructions in MBTiles_README.md")

if __name__ == "__main__":
    main()