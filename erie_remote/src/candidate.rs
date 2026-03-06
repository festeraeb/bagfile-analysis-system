//! Target candidate definition and shared geometry helpers.

use std::fmt;

/// The primary magnetic candidate — 305 nT dipolar anomaly, composite score 99/100.
/// Source: NRCan aeromag + USGS NAMA grids, processed by the Bagrecovery pipeline.
/// This is the coordinate output of the real pipeline run; it is NOT synthetic.
pub const CANDIDATE: Candidate = Candidate {
    lat: 42.4250,
    lon: -80.8130,
    amplitude_nt: 305.0,
    label: "Tier1-ERIE-MB2",
};

/// WGS84 decimal degrees, amplitude in nanoTesla.
#[derive(Debug, Clone, Copy)]
pub struct Candidate {
    pub lat: f64,
    pub lon: f64,
    pub amplitude_nt: f64,
    pub label: &'static str,
}

impl fmt::Display for Candidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{} ({:.4}°N, {:.4}°W)  {:.0} nT",
            self.label, self.lat, self.lon.abs(), self.amplitude_nt
        )
    }
}

/// Haversine distance in kilometres.
pub fn haversine_km(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let r = 6371.0_f64;
    let dlat = (lat2 - lat1).to_radians();
    let dlon = (lon2 - lon1).to_radians();
    let a = (dlat / 2.0).sin().powi(2)
        + lat1.to_radians().cos() * lat2.to_radians().cos() * (dlon / 2.0).sin().powi(2);
    r * 2.0 * a.sqrt().atan2((1.0 - a).sqrt())
}

/// A snug bounding box around the candidate — used for all data fetches.
pub struct BoundingBox {
    pub min_lat: f64,
    pub max_lat: f64,
    pub min_lon: f64,
    pub max_lon: f64,
}

impl BoundingBox {
    /// Create a box ± `half_deg` degrees around a point.
    pub fn around(lat: f64, lon: f64, half_deg: f64) -> Self {
        BoundingBox {
            min_lat: lat - half_deg,
            max_lat: lat + half_deg,
            min_lon: lon - half_deg,
            max_lon: lon + half_deg,
        }
    }

    /// ASF / Copernicus convention: "west,south,east,north"
    pub fn as_bbox_str(&self) -> String {
        format!(
            "{:.4},{:.4},{:.4},{:.4}",
            self.min_lon, self.min_lat, self.max_lon, self.max_lat
        )
    }

    /// ICGEM calcgrid convention: lat1/lat2/long1/long2
    pub fn as_icgem_params(&self) -> (f64, f64, f64, f64) {
        (self.min_lat, self.max_lat, self.min_lon, self.max_lon)
    }
}

/// Result from any of the three sensors, written to the multi-physics report.
#[derive(Debug, Clone, serde::Serialize)]
pub struct SensorResult {
    pub sensor: String,
    pub anomaly_detected: bool,
    pub value: f64,
    pub units: String,
    pub description: String,
    pub source_url: String,
}
