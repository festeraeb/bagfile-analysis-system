#!/usr/bin/env python3
"""
Database Coordinator for Wreck Detection Targets
Manages and coordinates wreck candidates across multiple BAG file scans
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CoordinatedTarget:
    """A coordinated wreck target with cross-scan validation"""
    target_id: int
    latitude: float
    longitude: float
    confidence_score: float
    detection_count: int  # How many scans detected this
    first_detected: str
    last_detected: str
    size_consensus: Dict  # Size statistics across detections
    signature_consensus: Dict  # Redaction signature patterns
    scan_sources: List[str]  # Which BAG files detected this
    priority_level: str  # 'high', 'medium', 'low'
    investigation_status: str  # 'pending', 'investigating', 'confirmed', 'rejected'
    notes: str

class DatabaseCoordinator:
    """Coordinates wreck detection results across multiple scans"""

    def __init__(self, db_path: str = 'wrecks.db'):
        self.db_path = db_path
        self._init_coordination_tables()

    def _init_coordination_tables(self):
        """Initialize coordination tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create coordination tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coordinated_targets (
                target_id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                confidence_score REAL NOT NULL,
                detection_count INTEGER DEFAULT 1,
                first_detected TEXT NOT NULL,
                last_detected TEXT NOT NULL,
                size_consensus TEXT,  -- JSON
                signature_consensus TEXT,  -- JSON
                scan_sources TEXT,  -- JSON
                priority_level TEXT DEFAULT 'medium',
                investigation_status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create target-scan mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS target_scan_mapping (
                target_id INTEGER,
                scan_id INTEGER,
                candidate_id INTEGER,
                confidence REAL,
                FOREIGN KEY (target_id) REFERENCES coordinated_targets(target_id),
                FOREIGN KEY (scan_id) REFERENCES bag_scans(id),
                FOREIGN KEY (candidate_id) REFERENCES wreck_candidates(id),
                PRIMARY KEY (target_id, scan_id, candidate_id)
            )
        ''')

        # Create target clusters for grouping nearby detections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS target_clusters (
                cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                centroid_lat REAL,
                centroid_lon REAL,
                target_count INTEGER,
                cluster_radius REAL,  -- meters
                cluster_type TEXT,  -- 'tight', 'spread', 'linear'
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cluster_membership (
                cluster_id INTEGER,
                target_id INTEGER,
                distance_from_centroid REAL,
                FOREIGN KEY (cluster_id) REFERENCES target_clusters(cluster_id),
                FOREIGN KEY (target_id) REFERENCES coordinated_targets(target_id),
                PRIMARY KEY (cluster_id, target_id)
            )
        ''')

        conn.commit()
        conn.close()

    def coordinate_targets(self, max_distance_meters: float = 50.0) -> Dict:
        """Coordinate targets across all scans, merging nearby detections"""

        logger.info("Starting target coordination...")

        # Get all candidates from all scans
        candidates = self._get_all_candidates()

        if not candidates:
            logger.info("No candidates found to coordinate")
            return {'coordinated_targets': 0, 'clusters': 0}

        # Group candidates into potential targets
        target_groups = self._group_nearby_candidates(candidates, max_distance_meters)

        # Create/update coordinated targets
        coordinated_targets = []
        for group in target_groups:
            target = self._create_coordinated_target(group)
            coordinated_targets.append(target)

        # Identify and create clusters
        clusters = self._identify_clusters(coordinated_targets)

        # Store coordination results
        self._store_coordination_results(coordinated_targets, clusters)

        logger.info(f"Coordination complete: {len(coordinated_targets)} targets, {len(clusters)} clusters")

        return {
            'coordinated_targets': len(coordinated_targets),
            'clusters': len(clusters),
            'targets': [self._target_to_dict(t) for t in coordinated_targets],
            'cluster_summary': self._cluster_summary(clusters)
        }

    def _get_all_candidates(self) -> List[Dict]:
        """Get all wreck candidates from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                wc.id as candidate_id,
                wc.scan_id,
                bs.file_name,
                wc.latitude,
                wc.longitude,
                wc.size_sq_meters,
                wc.size_sq_feet,
                wc.confidence,
                wc.method,
                wc.anomaly_score,
                wc.shape_complexity,
                wc.depth_gradient,
                bs.scan_timestamp,
                GROUP_CONCAT(rs.signature_type || ':' || rs.confidence) as signatures
            FROM wreck_candidates wc
            JOIN bag_scans bs ON wc.scan_id = bs.id
            LEFT JOIN redaction_signatures rs ON rs.candidate_id = wc.id
            GROUP BY wc.id, wc.scan_id, bs.file_name, wc.latitude, wc.longitude,
                     wc.size_sq_meters, wc.size_sq_feet, wc.confidence, wc.method,
                     wc.anomaly_score, wc.shape_complexity, wc.depth_gradient, bs.scan_timestamp
            ORDER BY wc.confidence DESC
        ''')

        candidates = []
        for row in cursor.fetchall():
            candidate = {
                'candidate_id': row[0],
                'scan_id': row[1],
                'file_name': row[2],
                'latitude': row[3],
                'longitude': row[4],
                'size_sq_meters': row[5],
                'size_sq_feet': row[6],
                'confidence': row[7],
                'method': row[8],
                'anomaly_score': row[9],
                'shape_complexity': row[10],
                'depth_gradient': row[11],
                'scan_timestamp': row[12],
                'signatures': row[13].split(',') if row[13] else []
            }
            candidates.append(candidate)

        conn.close()
        return candidates

    def _group_nearby_candidates(self, candidates: List[Dict], max_distance: float) -> List[List[Dict]]:
        """Group candidates that are within max_distance of each other"""
        groups = []
        used = set()

        for i, candidate1 in enumerate(candidates):
            if i in used:
                continue

            group = [candidate1]
            used.add(i)

            for j, candidate2 in enumerate(candidates):
                if j in used or j == i:
                    continue

                distance = self._haversine_distance(
                    candidate1['latitude'], candidate1['longitude'],
                    candidate2['latitude'], candidate2['longitude']
                )

                if distance <= max_distance:
                    group.append(candidate2)
                    used.add(j)

            groups.append(group)

        return groups

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using haversine formula"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Earth's radius in meters

        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def _create_coordinated_target(self, candidate_group: List[Dict]) -> CoordinatedTarget:
        """Create a coordinated target from a group of candidates"""

        # Calculate consensus position (weighted by confidence)
        total_weight = sum(c['confidence'] for c in candidate_group)
        avg_lat = sum(c['latitude'] * c['confidence'] for c in candidate_group) / total_weight
        avg_lon = sum(c['longitude'] * c['confidence'] for c in candidate_group) / total_weight

        # Calculate consensus confidence
        confidence_score = min(1.0, sum(c['confidence'] for c in candidate_group) / len(candidate_group) * 1.2)

        # Size consensus
        sizes_m2 = [c['size_sq_meters'] for c in candidate_group if c['size_sq_meters']]
        sizes_ft2 = [c['size_sq_feet'] for c in candidate_group if c['size_sq_feet']]

        size_consensus = {
            'mean_m2': sum(sizes_m2) / len(sizes_m2) if sizes_m2 else None,
            'mean_ft2': sum(sizes_ft2) / len(sizes_ft2) if sizes_ft2 else None,
            'std_m2': self._calculate_std(sizes_m2),
            'std_ft2': self._calculate_std(sizes_ft2),
            'range_m2': [min(sizes_m2), max(sizes_m2)] if sizes_m2 else None,
            'range_ft2': [min(sizes_ft2), max(sizes_ft2)] if sizes_ft2 else None
        }

        # Signature consensus
        all_signatures = []
        for candidate in candidate_group:
            all_signatures.extend(candidate['signatures'])

        signature_counts = defaultdict(int)
        for sig in all_signatures:
            if sig:
                sig_type = sig.split(':')[0] if ':' in sig else sig
                signature_counts[sig_type] += 1

        signature_consensus = dict(signature_counts)

        # Scan sources
        scan_sources = list(set(c['file_name'] for c in candidate_group))

        # Timestamps
        timestamps = [c['scan_timestamp'] for c in candidate_group]
        first_detected = min(timestamps)
        last_detected = max(timestamps)

        # Priority level based on confidence, detection count, and signatures
        detection_count = len(candidate_group)
        signature_strength = sum(signature_consensus.values())

        if confidence_score > 0.8 and detection_count >= 3:
            priority_level = 'high'
        elif confidence_score > 0.6 or signature_strength > 5:
            priority_level = 'medium'
        else:
            priority_level = 'low'

        return CoordinatedTarget(
            target_id=0,  # Will be set when stored
            latitude=avg_lat,
            longitude=avg_lon,
            confidence_score=confidence_score,
            detection_count=detection_count,
            first_detected=first_detected,
            last_detected=last_detected,
            size_consensus=size_consensus,
            signature_consensus=signature_consensus,
            scan_sources=scan_sources,
            priority_level=priority_level,
            investigation_status='pending',
            notes=f"Coordinated from {detection_count} detections across {len(scan_sources)} scans"
        )

    def _calculate_std(self, values: List[float]) -> Optional[float]:
        """Calculate standard deviation"""
        if len(values) < 2:
            return None
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _identify_clusters(self, targets: List[CoordinatedTarget]) -> List[Dict]:
        """Identify clusters of targets"""
        clusters = []

        # Simple clustering: group targets within 200m
        cluster_distance = 200.0  # meters
        used_targets = set()

        for i, target1 in enumerate(targets):
            if i in used_targets:
                continue

            cluster_targets = [target1]
            used_targets.add(i)

            cluster_lats = [target1.latitude]
            cluster_lons = [target1.longitude]

            for j, target2 in enumerate(targets):
                if j in used_targets or j == i:
                    continue

                # Check distance to cluster centroid
                centroid_lat = sum(cluster_lats) / len(cluster_lats)
                centroid_lon = sum(cluster_lons) / len(cluster_lons)

                distance = self._haversine_distance(
                    centroid_lat, centroid_lon,
                    target2.latitude, target2.longitude
                )

                if distance <= cluster_distance:
                    cluster_targets.append(target2)
                    used_targets.add(j)
                    cluster_lats.append(target2.latitude)
                    cluster_lons.append(target2.longitude)

            if len(cluster_targets) > 1:
                # Calculate cluster properties
                final_centroid_lat = sum(t.latitude for t in cluster_targets) / len(cluster_targets)
                final_centroid_lon = sum(t.longitude for t in cluster_targets) / len(cluster_targets)

                # Calculate spread
                distances = []
                for t in cluster_targets:
                    dist = self._haversine_distance(final_centroid_lat, final_centroid_lon,
                                                   t.latitude, t.longitude)
                    distances.append(dist)

                max_spread = max(distances) if distances else 0

                # Determine cluster type
                if max_spread < 50:
                    cluster_type = 'tight'
                elif max_spread < 150:
                    cluster_type = 'spread'
                else:
                    cluster_type = 'linear'

                cluster = {
                    'centroid_lat': final_centroid_lat,
                    'centroid_lon': final_centroid_lon,
                    'target_count': len(cluster_targets),
                    'cluster_radius': max_spread,
                    'cluster_type': cluster_type,
                    'targets': [t.target_id for t in cluster_targets]
                }
                clusters.append(cluster)

        return clusters

    def _store_coordination_results(self, targets: List[CoordinatedTarget], clusters: List[Dict]):
        """Store coordination results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clear existing coordination data
        cursor.execute('DELETE FROM coordinated_targets')
        cursor.execute('DELETE FROM target_scan_mapping')
        cursor.execute('DELETE FROM target_clusters')
        cursor.execute('DELETE FROM cluster_membership')

        # Store coordinated targets
        for target in targets:
            cursor.execute('''
                INSERT INTO coordinated_targets
                (latitude, longitude, confidence_score, detection_count, first_detected, last_detected,
                 size_consensus, signature_consensus, scan_sources, priority_level, investigation_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                target.latitude,
                target.longitude,
                target.confidence_score,
                target.detection_count,
                target.first_detected,
                target.last_detected,
                json.dumps(target.size_consensus),
                json.dumps(target.signature_consensus),
                json.dumps(target.scan_sources),
                target.priority_level,
                target.investigation_status,
                target.notes
            ))

            target.target_id = cursor.lastrowid

            # Store target-scan mappings (this would need to be implemented based on candidate groups)

        # Store clusters
        for cluster in clusters:
            cursor.execute('''
                INSERT INTO target_clusters
                (centroid_lat, centroid_lon, target_count, cluster_radius, cluster_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                cluster['centroid_lat'],
                cluster['centroid_lon'],
                cluster['target_count'],
                cluster['cluster_radius'],
                cluster['cluster_type']
            ))

            cluster_id = cursor.lastrowid

            # Store cluster membership
            for target_id in cluster['targets']:
                cursor.execute('''
                    INSERT INTO cluster_membership (cluster_id, target_id, distance_from_centroid)
                    VALUES (?, ?, ?)
                ''', (
                    cluster_id,
                    target_id,
                    self._haversine_distance(
                        cluster['centroid_lat'], cluster['centroid_lon'],
                        next(t.latitude for t in targets if t.target_id == target_id),
                        next(t.longitude for t in targets if t.target_id == target_id)
                    )
                ))

        conn.commit()
        conn.close()

    def _target_to_dict(self, target: CoordinatedTarget) -> Dict:
        """Convert target to dictionary"""
        return {
            'target_id': target.target_id,
            'latitude': target.latitude,
            'longitude': target.longitude,
            'confidence_score': target.confidence_score,
            'detection_count': target.detection_count,
            'first_detected': target.first_detected,
            'last_detected': target.last_detected,
            'size_consensus': target.size_consensus,
            'signature_consensus': target.signature_consensus,
            'scan_sources': target.scan_sources,
            'priority_level': target.priority_level,
            'investigation_status': target.investigation_status,
            'notes': target.notes
        }

    def _cluster_summary(self, clusters: List[Dict]) -> Dict:
        """Generate cluster summary"""
        if not clusters:
            return {'total_clusters': 0}

        cluster_types = defaultdict(int)
        for cluster in clusters:
            cluster_types[cluster['cluster_type']] += 1

        return {
            'total_clusters': len(clusters),
            'cluster_types': dict(cluster_types),
            'largest_cluster': max(clusters, key=lambda c: c['target_count'])['target_count'] if clusters else 0
        }

    def export_coordinated_targets(self, output_file: str, format: str = 'kml') -> str:
        """Export coordinated targets to KML/KMZ"""
        # Get coordinated targets
        targets = self._get_coordinated_targets()

        if not targets:
            logger.warning("No coordinated targets to export")
            return ""

        if format.lower() == 'kml':
            return self._export_targets_kml(targets, output_file)
        elif format.lower() == 'kmz':
            return self._export_targets_kmz(targets, output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _get_coordinated_targets(self) -> List[Dict]:
        """Get all coordinated targets from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM coordinated_targets ORDER BY confidence_score DESC
        ''')

        targets = []
        for row in cursor.fetchall():
            target = dict(row)
            # Parse JSON fields
            target['size_consensus'] = json.loads(target['size_consensus'] or '{}')
            target['signature_consensus'] = json.loads(target['signature_consensus'] or '{}')
            target['scan_sources'] = json.loads(target['scan_sources'] or '[]')
            targets.append(target)

        conn.close()
        return targets

    def _export_targets_kml(self, targets: List[Dict], output_file: str) -> str:
        """Export targets to KML format"""
        kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Coordinated Wreck Detection Targets</name>
    <description>Coordinated and validated wreck detection targets across multiple BAG file scans</description>

    <!-- Styles -->
    <Style id="highPriorityStyle">
      <IconStyle>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/danger.png</href></Icon>
        <scale>1.4</scale>
        <color>ff0000ff</color>
      </IconStyle>
      <LabelStyle><scale>1.0</scale><color>ff0000ff</color></LabelStyle>
    </Style>

    <Style id="mediumPriorityStyle">
      <IconStyle>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/caution.png</href></Icon>
        <scale>1.2</scale>
        <color>ffff00ff</color>
      </IconStyle>
      <LabelStyle><scale>0.8</scale><color>ffff00ff</color></LabelStyle>
    </Style>

    <Style id="lowPriorityStyle">
      <IconStyle>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/question.png</href></Icon>
        <scale>1.0</scale>
        <color>ff00ff00</color>
      </IconStyle>
      <LabelStyle><scale>0.6</scale><color>ff00ff00</color></LabelStyle>
    </Style>
'''

        # Group by priority
        priority_groups = defaultdict(list)
        for target in targets:
            priority_groups[target['priority_level']].append(target)

        for priority in ['high', 'medium', 'low']:
            if priority not in priority_groups:
                continue

            style_map = {
                'high': '#highPriorityStyle',
                'medium': '#mediumPriorityStyle',
                'low': '#lowPriorityStyle'
            }

            kml_content += f'''
    <Folder>
      <name>{priority.title()} Priority Targets</name>
      <description>{priority.title()} priority coordinated wreck detection targets</description>
'''

            for target in priority_groups[priority]:
                desc = f"""
      <![CDATA[
      <div style="font-family: Arial; max-width: 400px;">
        <h3>Target #{target['target_id']} ({target['priority_level'].title()} Priority)</h3>
        <table style="border-collapse: collapse; width: 100%;">
          <tr><td><b>Confidence:</b></td><td>{target['confidence_score']:.3f}</td></tr>
          <tr><td><b>Detection Count:</b></td><td>{target['detection_count']}</td></tr>
          <tr><td><b>Status:</b></td><td>{target['investigation_status'].title()}</td></tr>
          <tr><td><b>First Detected:</b></td><td>{target['first_detected'][:10]}</td></tr>
          <tr><td><b>Last Detected:</b></td><td>{target['last_detected'][:10]}</td></tr>
"""

                if target['size_consensus'].get('mean_m2'):
                    desc += f"""
          <tr><td><b>Size (mean):</b></td><td>{target['size_consensus']['mean_m2']:.1f} m²</td></tr>
"""

                if target['signature_consensus']:
                    desc += f"""
          <tr><td colspan="2"><b>Redaction Signatures:</b></td></tr>
"""
                    for sig_type, count in target['signature_consensus'].items():
                        desc += f"""
          <tr><td>{sig_type}:</td><td>{count} detections</td></tr>
"""

                desc += f"""
          <tr><td><b>Scan Sources:</b></td><td>{len(target['scan_sources'])} files</td></tr>
          <tr><td colspan="2"><b>Notes:</b></td></tr>
          <tr><td colspan="2">{target['notes']}</td></tr>
        </table>
      </div>
      ]]>
"""

                kml_content += f"""
      <Placemark>
        <name>Target {target['target_id']} (conf: {target['confidence_score']:.2f})</name>
        <description>{desc}</description>
        <styleUrl>{style_map[priority]}</styleUrl>
        <Point>
          <coordinates>{target['longitude']:.6f},{target['latitude']:.6f},0</coordinates>
        </Point>
      </Placemark>
"""

            kml_content += """
    </Folder>
"""

        kml_content += """
  </Document>
</kml>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(kml_content)

        logger.info(f"Exported {len(targets)} coordinated targets to {output_file}")
        return output_file

    def _export_targets_kmz(self, targets: List[Dict], output_file: str) -> str:
        """Export targets to KMZ format"""
        import zipfile
        import tempfile

        # Create temporary KML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kml', delete=False) as temp_kml:
            temp_kml_path = temp_kml.name
            self._export_targets_kml(targets, temp_kml_path)

        # Create KMZ
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as kmz:
            kmz.write(temp_kml_path, 'doc.kml')

        # Clean up
        os.unlink(temp_kml_path)

        logger.info(f"Exported {len(targets)} coordinated targets to {output_file}")
        return output_file

    def get_coordination_summary(self) -> Dict:
        """Get summary of coordination results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get target statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_targets,
                AVG(confidence_score) as avg_confidence,
                SUM(detection_count) as total_detections,
                COUNT(CASE WHEN priority_level = 'high' THEN 1 END) as high_priority,
                COUNT(CASE WHEN priority_level = 'medium' THEN 1 END) as medium_priority,
                COUNT(CASE WHEN priority_level = 'low' THEN 1 END) as low_priority
            FROM coordinated_targets
        ''')

        target_stats = cursor.fetchone()

        # Get cluster statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_clusters,
                AVG(target_count) as avg_targets_per_cluster,
                MAX(target_count) as max_targets_per_cluster
            FROM target_clusters
        ''')

        cluster_stats = cursor.fetchone()

        conn.close()

        return {
            'total_targets': target_stats[0] or 0,
            'avg_confidence': target_stats[1] or 0,
            'total_detections': target_stats[2] or 0,
            'priority_breakdown': {
                'high': target_stats[3] or 0,
                'medium': target_stats[4] or 0,
                'low': target_stats[5] or 0
            },
            'cluster_stats': {
                'total_clusters': cluster_stats[0] or 0,
                'avg_targets_per_cluster': cluster_stats[1] or 0,
                'max_targets_per_cluster': cluster_stats[2] or 0
            }
        }</content>
<parameter name="filePath">c:\Temp\Garminjunk\HistoryofCESARSNIFFERBAGFILE\bagfilework\database_coordinator.py