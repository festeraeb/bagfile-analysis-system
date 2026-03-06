//! ICESat-2 ATL13 water-surface elevation scraper + persistent anomaly detector.
//!
//! # Data source
//!
//! NASA CMR -> NSIDC DAAC
//!   Search: https://cmr.earthdata.nasa.gov/search/granules.json
//!   Product: ATL13 (Inland Water Surface Height with Statistics), version 006
//!   Format: HDF5
//!   Authentication: NASA Earthdata Bearer token
//!
//! HDF5 paths (per ground track gt1l/gt1r/gt2l/gt2r/gt3l/gt3r):
//!   /gtXy/inland_water/lat           f64[n]
//!   /gtXy/inland_water/lon           f64[n]
//!   /gtXy/inland_water/ht_water_surf f64[n]  WGS84 ellipsoidal height (m)
//!   /gtXy/inland_water/delta_time    f64[n]  secs since 2018-01-01 GPS
//!
//! # Algorithm
//!
//! 1. CMR search for all ATL13 granules over Lake Erie box, 2018-present.
//! 2. For each granule + 6 ground tracks, extract measurements within
//!    SEARCH_RADIUS_KM of the candidate.
//! 3. Bin to 0.001 degree (~100 m) grid over Central Basin.
//! 4. Compute per-cell: median, IQR, temporal std.
//! 5. Flag cells with persistent elevation > basin median + 2*IQR in >50% of passes.

use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

use crate::candidate::{haversine_km, BoundingBox, Candidate, SensorResult};

const CMR_SEARCH_URL: &str = "https://cmr.earthdata.nasa.gov/search/granules.json";
const ATL13_SHORT_NAME: &str  = "ATL13";
const ATL13_VERSION:    &str  = "006";
const SEARCH_RADIUS_KM: f64   = 1.5;
const PERSISTENCE_THRESHOLD:  f64 = 0.5;
const IQR_MULTIPLIER:         f64 = 2.0;

/// Ground track identifiers in ATL13 HDF5 (all six beams)
#[cfg(feature = "hdf5-support")]
const GROUND_TRACKS: &[&str] = &["gt1l", "gt1r", "gt2l", "gt2r", "gt3l", "gt3r"];

// -- CMR granule search --------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct CmrGranule {
    pub title: String,
    pub links: Vec<CmrLink>,
}

#[derive(Debug, Deserialize)]
pub struct CmrLink {
    pub rel:  Option<String>,
    pub href: String,
}

impl CmrGranule {
    pub fn download_url(&self) -> Option<&str> {
        self.links.iter()
            .find(|l| l.href.ends_with(".h5") || l.href.ends_with(".h5.nc"))
            .map(|l| l.href.as_str())
    }
}

pub async fn search_cmr(
    bbox:      &BoundingBox,
    start_date: &str,
    end_date:   &str,
    max_pages:  usize,
    client:     &reqwest::Client,
) -> Result<Vec<CmrGranule>> {
    let mut all: Vec<CmrGranule> = Vec::new();
    let page_size = 200usize;

    for page in 1..=max_pages {
        let url = format!(
            "{base}?short_name={sn}&version={ver}\
             &bounding_box={bbox}\
             &temporal[]={start},{end}\
             &page_size={ps}&page_num={pn}",
            base  = CMR_SEARCH_URL,
            sn    = ATL13_SHORT_NAME,  ver = ATL13_VERSION,
            bbox  = bbox.as_bbox_str(),
            start = start_date,        end = end_date,
            ps    = page_size,         pn  = page,
        );
        tracing::info!("CMR search page {page}: {url}");
        let resp = client.get(&url).send().await.context("CMR request")?;
        if !resp.status().is_success() {
            return Err(anyhow!("CMR returned HTTP {}", resp.status()));
        }
        let body: serde_json::Value = resp.json().await?;
        let items = body.pointer("/feed/entry")
            .and_then(|v| v.as_array()).cloned().unwrap_or_default();
        if items.is_empty() { break; }
        for item in &items {
            match serde_json::from_value::<CmrGranule>(item.clone()) {
                Ok(g)  => all.push(g),
                Err(e) => tracing::warn!("CMR granule parse error: {e}"),
            }
        }
        if items.len() < page_size { break; }
    }
    tracing::info!("CMR search: {} ATL13 granules found", all.len());
    Ok(all)
}

// -- HDF5 parsing (feature-gated) ----------------------------------------------

#[derive(Debug, Clone)]
pub struct AtlMeasurement {
    pub lat: f64, pub lon: f64,
    pub ht:  f64,  // WGS84 ellipsoidal height (m)
    pub t:   f64,  // secs since 2018-01-01 GPS
}

pub fn parse_atl13(h5_path: &Path) -> Result<Vec<AtlMeasurement>> {
    #[cfg(feature = "hdf5-support")]
    { parse_atl13_hdf5(h5_path) }
    #[cfg(not(feature = "hdf5-support"))]
    {
        tracing::warn!(
            "hdf5-support feature not enabled; ATL13 parse skipped for {}",
            h5_path.display()
        );
        Ok(Vec::new())
    }
}

#[cfg(feature = "hdf5-support")]
fn parse_atl13_hdf5(h5_path: &Path) -> Result<Vec<AtlMeasurement>> {
    let file = hdf5::File::open(h5_path)
        .with_context(|| format!("HDF5 open: {}", h5_path.display()))?;
    let mut out = Vec::new();
    for track in GROUND_TRACKS {
        let iw_path = format!("{track}/inland_water");
        let group = match file.group(&iw_path) { Ok(g) => g, Err(_) => continue };
        let read = |ds: &str| -> Result<Vec<f64>> {
            Ok(group.dataset(ds)?.read_1d::<f64>()?.to_vec())
        };
        let lats = read("lat")?;  let lons = read("lon")?;
        let hts  = read("ht_water_surf")?;  let ts = read("delta_time")?;
        let n = lats.len().min(lons.len()).min(hts.len()).min(ts.len());
        for i in 0..n {
            if hts[i].abs() > 1_000.0 { continue; } // fill value
            out.push(AtlMeasurement { lat: lats[i], lon: lons[i], ht: hts[i], t: ts[i] });
        }
    }
    Ok(out)
}

// -- Elevation stack analyser --------------------------------------------------

/// One grid point at 0.001 degree resolution
#[allow(dead_code)]
struct GridCell {
    lat_idx: i32,
    lon_idx: i32,
    values:  Vec<f64>,
}

#[allow(dead_code)]
fn grid_key(lat: f64, lon: f64) -> (i32, i32) {
    ((lat * 1000.0).round() as i32, (lon * 1000.0).round() as i32)
}

fn median(v: &mut Vec<f64>) -> f64 {
    if v.is_empty() { return 0.0; }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = v.len();
    if n % 2 == 0 { (v[n/2 - 1] + v[n/2]) / 2.0 } else { v[n/2] }
}

fn iqr(v: &mut Vec<f64>) -> f64 {
    if v.len() < 4 { return 0.0; }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = v.len();
    v[3 * n / 4] - v[n / 4]
}

#[derive(Debug, Serialize)]
pub struct Icesat2Stack {
    pub n_granules:          usize,
    pub n_measurements:      usize,
    pub median_ht_m:         f64,
    pub iqr_ht_m:            f64,
    pub basin_median_m:      f64,
    pub relative_anomaly_m:  f64,
    pub persistence_fraction: f64,
    pub anomaly_flagged:     bool,
}

impl Icesat2Stack {
    pub fn to_sensor_result(&self) -> SensorResult {
        SensorResult {
            sensor: "ICESat-2 ATL13 Water Surface Elevation".to_string(),
            anomaly_detected: self.anomaly_flagged,
            value: self.relative_anomaly_m,
            units: "m (vs basin median)".to_string(),
            description: format!(
                "n_granules={} n_meas={} median={:.3}m IQR={:.3}m \
                 basin={:.3}m rel={:+.3}m persistence={:.2} flagged={}",
                self.n_granules, self.n_measurements,
                self.median_ht_m, self.iqr_ht_m, self.basin_median_m,
                self.relative_anomaly_m, self.persistence_fraction, self.anomaly_flagged,
            ),
            source_url: CMR_SEARCH_URL.to_string(),
        }
    }

    pub fn from_measurements(
        all_measurements: &[AtlMeasurement],
        candidate: &Candidate,
        n_granules: usize,
    ) -> Self {
        let mut cand_vals: Vec<f64> = Vec::new();
        let mut basin_vals: Vec<f64> = Vec::new();

        for m in all_measurements {
            let d = haversine_km(candidate.lat, candidate.lon, m.lat, m.lon);
            basin_vals.push(m.ht);
            if d <= SEARCH_RADIUS_KM { cand_vals.push(m.ht); }
        }

        let n_measurements = cand_vals.len();
        let mut cand_sorted  = cand_vals.clone();
        let mut basin_sorted = basin_vals.clone();
        let med_cand  = median(&mut cand_sorted);
        let iqr_cand  = iqr(&mut cand_sorted);
        let med_basin = median(&mut basin_sorted);
        let relative  = med_cand - med_basin;

        let mut monthly: HashMap<String, Vec<f64>> = HashMap::new();
        for m in all_measurements {
            let months_since = (m.t / (30.5 * 86400.0)) as i64;
            let d = haversine_km(candidate.lat, candidate.lon, m.lat, m.lon);
            if d <= SEARCH_RADIUS_KM {
                monthly.entry(months_since.to_string()).or_default().push(m.ht);
            }
        }
        let threshold  = med_basin + IQR_MULTIPLIER * iqr_cand;
        let n_passes   = monthly.len();
        let n_flagged  = monthly.values().filter(|vals| {
            let mean = vals.iter().sum::<f64>() / vals.len() as f64;
            mean > threshold
        }).count();
        let persistence = if n_passes > 0 { n_flagged as f64 / n_passes as f64 } else { 0.0 };
        let anomaly_flagged = persistence > PERSISTENCE_THRESHOLD && n_measurements >= 3;

        Icesat2Stack {
            n_granules, n_measurements,
            median_ht_m: med_cand, iqr_ht_m: iqr_cand,
            basin_median_m: med_basin, relative_anomaly_m: relative,
            persistence_fraction: persistence, anomaly_flagged,
        }
    }
}

// -- Download / cache ----------------------------------------------------------

pub fn cache_dir(data_root: &Path) -> PathBuf { data_root.join("icesat2_cache") }

pub async fn download_granule(url: &str, data_root: &Path, client: &reqwest::Client) -> Result<PathBuf> {
    let filename = url.split('/').last().unwrap_or("atl13.h5");
    let out_path = cache_dir(data_root).join(filename);
    if out_path.exists() { return Ok(out_path); }
    tracing::info!("Downloading ATL13 granule: {filename}");
    let resp  = client.get(url).send().await.context("ATL13 download")?;
    if !resp.status().is_success() {
        return Err(anyhow!("ATL13 download HTTP {}: {url}", resp.status()));
    }
    let bytes = resp.bytes().await?;
    std::fs::write(&out_path, &bytes)?;
    Ok(out_path)
}

// -- Top-level runner ----------------------------------------------------------

pub async fn run(
    candidate:       &Candidate,
    data_root:       &Path,
    earthdata_token: Option<&str>,
    start_date:      &str,
    end_date:        &str,
    dry_run:         bool,
) -> Result<Icesat2Stack> {
    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert("User-Agent", "erie-remote/0.1".parse().unwrap());
    if let Some(tok) = earthdata_token {
        headers.insert(reqwest::header::AUTHORIZATION, format!("Bearer {tok}").parse().unwrap());
    }
    let client = reqwest::Client::builder()
        .default_headers(headers)
        .redirect(reqwest::redirect::Policy::limited(10))
        .build()?;

    let bbox      = BoundingBox::around(candidate.lat, candidate.lon, 1.0);
    let start_iso = format!("{start_date}T00:00:00Z");
    let end_iso   = format!("{end_date}T23:59:59Z");
    let granules  = search_cmr(&bbox, &start_iso, &end_iso, 20, &client).await?;
    tracing::info!("Found {} ATL13 granules", granules.len());

    if dry_run || granules.is_empty() {
        return Ok(Icesat2Stack::from_measurements(&[], candidate, granules.len()));
    }

    std::fs::create_dir_all(cache_dir(data_root))?;
    let n_granules    = granules.len();
    let mut all_meas: Vec<AtlMeasurement> = Vec::new();

    for g in &granules {
        let Some(url) = g.download_url() else {
            tracing::warn!("No download URL for {}", g.title); continue;
        };
        let h5_path = match download_granule(url, data_root, &client).await {
            Ok(p)  => p,
            Err(e) => { tracing::warn!("{}: download failed: {e}", g.title); continue; }
        };
        let meas = match parse_atl13(&h5_path) {
            Ok(m)  => m,
            Err(e) => { tracing::warn!("{}: parse failed: {e}", g.title); continue; }
        };
        tracing::info!("{}: {} measurements", g.title, meas.len());
        all_meas.extend(meas);
    }

    tracing::info!("Total ATL13 measurements: {}", all_meas.len());
    Ok(Icesat2Stack::from_measurements(&all_meas, candidate, n_granules))
}
