//! GOCE gravity gradient scraper + magnetic-vs-gravity azimuth comparator.
//!
//! # Data source
//!
//! ICGEM (International Centre for Global Earth Models), GFZ Potsdam
//!   Service URL: http://icgem.gfz-potsdam.de/calcgrid
//!   Model: EIGEN-6C4  (combines GOCE + GRACE + EGM2008; best available)
//!   Functional: gravity anomaly (free-air, mGal)
//!   No authentication required.
//!
//! # Physical detectability note
//!
//! Direct wreck detection is impossible:
//!   - Ship mass ~3000 tons iron, Drho = 6074 kg/m3, V_eff = 500 m3
//!   - Point mass at 24 m depth: Dg = G*M/r^2 = 6.674e-11 * 3e6 / 576 = 0.35 uGal
//!   - EIGEN-6C4 noise floor: ~1000 uGal (1 mGal)
//!
//! Valid use: tectonic lineament / Precambrian basement density ridges ARE
//! detectable at ~10km resolution.  If the gravity gradient AZIMUTH at the
//! candidate matches the magnetic dipole strike (+/-30 deg), this is strong
//! evidence that both anomalies share a common geological cause (hard-bottom
//! nav hazard zone) - which increases confidence in the magnetic hit.

use anyhow::{anyhow, Context, Result};
use serde::Serialize;
use std::path::{Path, PathBuf};

use crate::candidate::{BoundingBox, Candidate, SensorResult};

const ICGEM_URL:         &str = "http://icgem.gfz-potsdam.de/calcgrid";
const GRAVITY_MODEL:     &str = "EIGEN-6C4";
const GRID_STEP_DEG:     f64  = 0.05;    // ~5 km node spacing
const GRID_HALF_DEG:     f64  = 0.5;     // 1 degree box
/// Expected magnetic dipole strike for M&B No.2 candidate (degrees from N)
const MAG_DIPOLE_STRIKE_DEG: f64 = 340.0;
const AZIMUTH_TOLERANCE_DEG: f64 = 30.0;

// -- GDF text parser -----------------------------------------------------------

/// One grid point from the ICGEM GDF text format.
#[derive(Debug, Clone)]
pub struct GravityPoint {
    pub lat:   f64,
    pub lon:   f64,
    pub value: f64,  // free-air gravity anomaly (mGal)
}

/// Parse ICGEM GDF text.  Data begins after "end_of_head" marker.
pub fn parse_gdf(text: &str) -> Vec<GravityPoint> {
    let mut in_data = false;
    let mut points  = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.starts_with("end_of_head") { in_data = true; continue; }
        if !in_data || line.is_empty() || line.starts_with('#') { continue; }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 3 {
            if let (Ok(lat), Ok(lon), Ok(val)) = (
                parts[0].parse::<f64>(), parts[1].parse::<f64>(), parts[2].parse::<f64>(),
            ) { points.push(GravityPoint { lat, lon, value: val }); }
        }
    }
    points
}

// -- Gravity gradient analysis -------------------------------------------------

/// Bilinear interpolation at arbitrary (lat, lon).
pub fn interpolate(grid: &[GravityPoint], lat: f64, lon: f64) -> Option<f64> {
    let step = GRID_STEP_DEG;
    let lat0 = (lat / step).floor() * step;
    let lon0 = (lon / step).floor() * step;
    let find = |la: f64, lo: f64| -> Option<f64> {
        grid.iter()
            .find(|p| (p.lat - la).abs() < step * 0.6 && (p.lon - lo).abs() < step * 0.6)
            .map(|p| p.value)
    };
    let q00 = find(lat0, lon0)?;
    let q10 = find(lat0 + step, lon0)?;
    let q01 = find(lat0, lon0 + step)?;
    let q11 = find(lat0 + step, lon0 + step)?;
    let t = (lat - lat0) / step;
    let u = (lon - lon0) / step;
    Some(q00*(1.0-t)*(1.0-u) + q10*t*(1.0-u) + q01*(1.0-t)*u + q11*t*u)
}

/// Central-difference horizontal gradient at (lat, lon).  Returns (dg/dN, dg/dE).
pub fn horizontal_gradient(grid: &[GravityPoint], lat: f64, lon: f64) -> Option<(f64, f64)> {
    let dlat = GRID_STEP_DEG;
    let dlon = GRID_STEP_DEG;
    let g_n = interpolate(grid, lat + dlat, lon)?;
    let g_s = interpolate(grid, lat - dlat, lon)?;
    let g_e = interpolate(grid, lat, lon + dlon)?;
    let g_w = interpolate(grid, lat, lon - dlon)?;
    let dy_m = dlat * 2.0 * 111_320.0;
    let dx_m = dlon * 2.0 * 111_320.0 * lat.to_radians().cos();
    Some(((g_n - g_s) / dy_m, (g_e - g_w) / dx_m))
}

/// Gradient azimuth, degrees clockwise from north (0-360).
pub fn gradient_azimuth(grad_n: f64, grad_e: f64) -> f64 {
    (90.0 - grad_e.atan2(grad_n).to_degrees()).rem_euclid(360.0)
}

#[derive(Debug, Serialize)]
pub struct GravityResult {
    pub free_air_mgal:          f64,
    pub background_mean_mgal:   f64,
    pub relative_anomaly_mgal:  f64,
    pub grad_north:             f64,
    pub grad_east:              f64,
    pub grad_magnitude:         f64,
    pub gradient_azimuth_deg:   f64,
    pub mag_strike_deg:         f64,
    pub azimuth_delta_deg:      f64,
    /// True if delta <= AZIMUTH_TOLERANCE_DEG
    pub azimuth_concordant:     bool,
    pub n_grid_points:          usize,
}

impl GravityResult {
    pub fn to_sensor_result(&self) -> SensorResult {
        SensorResult {
            sensor: "GOCE/EIGEN-6C4 Free-Air Gravity Gradient".to_string(),
            anomaly_detected: self.azimuth_concordant,
            value: self.relative_anomaly_mgal,
            units: "mGal (vs basin background)".to_string(),
            description: format!(
                "Dg={:.3} mGal  grad_az={:.1} deg  mag_strike={:.1} deg  \
                 delta={:.1} deg  concordant={}  n_pts={}",
                self.relative_anomaly_mgal, self.gradient_azimuth_deg,
                self.mag_strike_deg, self.azimuth_delta_deg,
                self.azimuth_concordant, self.n_grid_points,
            ),
            source_url: ICGEM_URL.to_string(),
        }
    }

    pub fn from_grid(grid: &[GravityPoint], candidate: &Candidate) -> Result<Self> {
        let cand_g  = interpolate(grid, candidate.lat, candidate.lon)
            .ok_or_else(|| anyhow!("Candidate not covered by gravity grid"))?;
        let n_pts   = grid.len();
        let bg_mean = grid.iter().map(|p| p.value).sum::<f64>() / n_pts as f64;
        let relative = cand_g - bg_mean;
        let (grad_n, grad_e) = horizontal_gradient(grid, candidate.lat, candidate.lon)
            .ok_or_else(|| anyhow!("Cannot compute gradient - grid too small"))?;
        let grad_mag = (grad_n * grad_n + grad_e * grad_e).sqrt();
        let gaz = gradient_azimuth(grad_n, grad_e);
        let raw_delta = (gaz - MAG_DIPOLE_STRIKE_DEG).abs().rem_euclid(360.0);
        let delta     = raw_delta.min(360.0 - raw_delta);
        let concordant = delta <= AZIMUTH_TOLERANCE_DEG;
        Ok(GravityResult {
            free_air_mgal: cand_g, background_mean_mgal: bg_mean,
            relative_anomaly_mgal: relative, grad_north: grad_n, grad_east: grad_e,
            grad_magnitude: grad_mag, gradient_azimuth_deg: gaz,
            mag_strike_deg: MAG_DIPOLE_STRIKE_DEG, azimuth_delta_deg: delta,
            azimuth_concordant: concordant, n_grid_points: n_pts,
        })
    }
}

// -- Cache helpers -------------------------------------------------------------

pub fn cache_dir(data_root: &Path) -> PathBuf { data_root.join("gravity_cache") }

pub fn cache_path(data_root: &Path, bbox: &BoundingBox) -> PathBuf {
    cache_dir(data_root).join(format!(
        "eigen6c4_{:.2}_{:.2}_{:.2}_{:.2}_{:.3}.gdf",
        bbox.min_lat, bbox.max_lat, bbox.min_lon, bbox.max_lon, GRID_STEP_DEG,
    ))
}

// -- ICGEM fetch ---------------------------------------------------------------

/// Download free-air gravity grid from ICGEM calcgrid (no auth required).
pub async fn fetch_icgem_grid(bbox: &BoundingBox, client: &reqwest::Client) -> Result<String> {
    let (lat1, lat2, lon1, lon2) = bbox.as_icgem_params();
    let params = [
        ("model",       GRAVITY_MODEL),
        ("lat1",        &lat1.to_string()),
        ("lat2",        &lat2.to_string()),
        ("long1",       &lon1.to_string()),
        ("long2",       &lon2.to_string()),
        ("step",        &GRID_STEP_DEG.to_string()),
        ("functional",  "gravity"),
        ("unit",        "mgal"),
        ("ref_frame",   "GRS80"),
        ("tide_system", "tide_free"),
        ("format",      "gdf"),
    ];
    tracing::info!("Fetching ICGEM EIGEN-6C4 grid: lat {lat1:.2}-{lat2:.2}  lon {lon1:.2}-{lon2:.2}");
    let resp = client.get(ICGEM_URL).query(&params)
        .header("User-Agent", "erie-remote/0.1 (wreck-research)")
        .send().await.context("ICGEM request")?;
    if !resp.status().is_success() {
        let status = resp.status();
        let body   = resp.text().await.unwrap_or_default();
        return Err(anyhow!("ICGEM returned HTTP {status}: {body}"));
    }
    let text = resp.text().await.context("ICGEM response text")?;
    if text.trim().is_empty() || !text.contains("end_of_head") {
        return Err(anyhow!("ICGEM response not valid GDF format"));
    }
    tracing::info!("ICGEM grid: {} chars", text.len());
    Ok(text)
}

// -- Top-level runner ----------------------------------------------------------

pub async fn run(candidate: &Candidate, data_root: &Path, dry_run: bool) -> Result<GravityResult> {
    let client = reqwest::Client::builder()
        .user_agent("erie-remote/0.1 (wreck-research)").build()?;
    let bbox   = BoundingBox::around(candidate.lat, candidate.lon, GRID_HALF_DEG);
    std::fs::create_dir_all(cache_dir(data_root))?;
    let c_path = cache_path(data_root, &bbox);
    let gdf_text = if c_path.exists() {
        tracing::info!("Loading cached GOCE grid: {}", c_path.display());
        std::fs::read_to_string(&c_path).context("cached GDF read")?
    } else if dry_run {
        return Err(anyhow!("Dry run; no gravity data available"));
    } else {
        let text = fetch_icgem_grid(&bbox, &client).await?;
        std::fs::write(&c_path, &text)?;
        tracing::info!("Cached gravity grid -> {}", c_path.display());
        text
    };
    let grid = parse_gdf(&gdf_text);
    tracing::info!("Gravity grid: {} points", grid.len());
    if grid.is_empty() {
        return Err(anyhow!("GDF parsed to zero points"));
    }
    GravityResult::from_grid(&grid, candidate)
}
