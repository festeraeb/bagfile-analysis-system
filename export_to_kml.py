import sqlite3
import json
from datetime import datetime

def create_kml_header():
    """Create KML file header"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <name>Wreck Database - Coordinate Estimates and Newspaper Validations</name>
    <description>Historical shipwrecks with estimated coordinates and newspaper references</description>

    <!-- Style definitions -->
    <Style id="wreckStyle">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/danger.png</href>
        </Icon>
        <scale>1.2</scale>
      </IconStyle>
      <LabelStyle>
        <scale>0.8</scale>
      </LabelStyle>
    </Style>

    <Style id="obstructionStyle">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/caution.png</href>
        </Icon>
        <scale>1.1</scale>
      </IconStyle>
      <LabelStyle>
        <scale>0.7</scale>
      </LabelStyle>
    </Style>

    <Style id="estimatedStyle">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/question.png</href>
        </Icon>
        <scale>0.9</scale>
        <color>ff00ffff</color>
      </IconStyle>
      <LabelStyle>
        <scale>0.6</scale>
        <color>ff00ffff</color>
      </LabelStyle>
    </Style>
'''

def create_kml_placemark(feature):
    """Create a KML placemark for a feature"""
    feature_id = feature['id']
    name = feature['name'] or f"Feature {feature_id}"
    latitude = feature['latitude']
    longitude = feature['longitude']
    feature_type = feature['feature_type'] or 'Unknown'
    date = feature['date'] or 'Unknown'
    source = feature['source'] or 'Unknown'
    depth = feature['depth'] or 'Unknown'
    place_names = feature['historical_place_names'] or 'Unknown'
    newspaper_clip = feature['newspaper_clip'] or 'None'

    # Determine style based on type and coordinate source
    if 'estimated' in str(source).lower() or not latitude:
        style_url = "#estimatedStyle"
        coord_status = "Estimated"
    elif feature_type and 'wreck' in feature_type.lower():
        style_url = "#wreckStyle"
        coord_status = "Verified"
    else:
        style_url = "#obstructionStyle"
        coord_status = "Verified"

    # Create description
    description = f"""
    <![CDATA[
    <div style="font-family: Arial, sans-serif; max-width: 300px;">
        <h3>{name}</h3>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><td><b>Type:</b></td><td>{feature_type}</td></tr>
            <tr><td><b>Date:</b></td><td>{date}</td></tr>
            <tr><td><b>Depth:</b></td><td>{depth}</td></tr>
            <tr><td><b>Location:</b></td><td>{place_names}</td></tr>
            <tr><td><b>Coordinates:</b></td><td>{coord_status}</td></tr>
            <tr><td><b>Source:</b></td><td>{source}</td></tr>
            <tr><td><b>Newspaper Clip:</b></td><td>{'Yes' if newspaper_clip != 'None' else 'No'}</td></tr>
        </table>
        <p><i>Click to view newspaper validation</i></p>
    </div>
    ]]>
    """

    # Only create placemark if we have coordinates
    if latitude and longitude:
        return f"""
    <Placemark>
      <name>{name}</name>
      <description>{description}</description>
      <styleUrl>{style_url}</styleUrl>
      <Point>
        <coordinates>{longitude},{latitude},0</coordinates>
      </Point>
    </Placemark>
"""
    return ""

def create_kml_footer():
    """Create KML file footer"""
    return """
  </Document>
</kml>
"""

def export_to_kml():
    """Export database to KML format"""
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

    print(f"Exporting {len(features)} features with coordinates to KML...")

    kml_content = create_kml_header()

    for feature in features:
        feature_dict = dict(feature)
        kml_content += create_kml_placemark(feature_dict)

    kml_content += create_kml_footer()

    # Save KML file
    kml_filename = f"wreck_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.kml"
    with open(kml_filename, 'w', encoding='utf-8') as f:
        f.write(kml_content)

    print(f"KML file saved as: {kml_filename}")
    print("Open this file in Google Earth or any KML-compatible viewer.")

    return kml_filename

def main():
    export_to_kml()

if __name__ == "__main__":
    main()