
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
