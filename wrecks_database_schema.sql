-- SQLite schema for wrecks and obstructions database
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date TEXT,
    latitude REAL,
    longitude REAL,
    depth TEXT,
    feature_type TEXT,
    source TEXT,
    newspaper_clip TEXT,
    historical_place_names TEXT
);

-- Example insert
-- INSERT INTO features (name, date, latitude, longitude, depth, feature_type, source, newspaper_clip, historical_place_names)
-- VALUES ('Elva Candidate 1 (PDF Confirmed)', NULL, 45.849306, -84.613028, NULL, 'Wreck', 'robust_bag_scanner.py', NULL, NULL);
