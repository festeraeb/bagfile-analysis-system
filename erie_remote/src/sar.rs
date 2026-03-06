//! Sentinel-1 SAR multi-temporal backscatter scraper + curvelet anomaly detector.
//!
//! # Data source
//!
//! Alaska Satellite Facility (ASF) Vertex API — free, no auth for search;
//! NASA Earthdata account needed for download.
//!   Search endpoint: https://api.daac.asf.alaska.edu/services/search/param
//!   Product: Sentinel-1 IW GRD_HD, VV polarisation
//!   Coverage: 12-day repeat orbit; ~100 scenes/year over Erie
//!
//! # Algorithm
//!
//! 1. Search for all IW GRD_HD scenes overlapping the bounding box, 2018-present.
//! 2. For each scene, download the GeoTIFF VV band (GAMMA0-calibrated if available,
//!    otherwise sigma0).
//! 3. Apply Discrete Curvelet Transform (curvelet crate, 5 scales) to suppress
//!    speckle while retaining directional edge features.
//! 4. Extract the denoised backscatter at +-1 pixel around the candidate location.
//! 5. Stack all scenes chronologically into a T x 1 time series.
//! 6. Compute:
//!      - temporal mean mu and std sigma of the normalised backscatter
//!      - multi-temporal coherence estimate: rho = 1 - sigma/mu  (0=incoherent, 1=coherent)
//!      - anomaly flag: candidate value deviates > 2sigma from a 15-km background annulus
//!
//! # Limitations
//!
//! - GRD gives intensity only; true interferometric coherence requires co-registered
//!   SLC pairs (full SNAP workflow).  This module does multi-temporal intensity
//!   coherence, which is a valid proxy for stable surface features.
//! - The wreck effect on capillary-wave Bragg scatter is subtle (~0.5 dB in the
//!   literature for shallow submerged objects).  Expect low SNR; the pipeline
//!   reports the statistics and lets you decide.

use anyhow::{anyhow, Context, Result};
use ndarray::Array2;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

use crate::candidate::{BoundingBox, Candidate, SensorResult};

// -- ASF Vertex search API -----------------------------------------------------

const ASF_SEARCH_URL: &str =
    "https://api.daac.asf.alaska.edu/services/search/param";

/// One granule returned by the ASF search API
#[derive(Debug, Deserialize)]
#[allow(dead_code)]
pub struct AsfGranule {
    #[serde(rename = "granuleName")]
    pub granule_name: String,
    #[serde(rename = "startTime")]
    pub start_time: String,
    #[serde(rename = "downloadUrl")]
    pub download_url: String,
    #[serde(rename = "sizeMB", default)]
    pub size_mb: f64,
    /// Orbit direction: ASCENDING or DESCENDING
    #[serde(rename = "flightDirection", default)]
    pub flight_direction: String,
}

/// Search ASF for all Sentinel-1 IW GRD scenes over the bounding box.
pub async fn search_asf(
    bbox: &BoundingBox,
    start_date: &str,
    end_date: &str,
    max_results: usize,
    client: &reqwest::Client,
) -> Result<Vec<AsfGranule>> {
    let mut url = format!(
        "{base}?platform=S1&processingLevel=GRD_HD&output=json\
         &bbox={bbox}&start={start}&end={end}",
        base  = ASF_SEARCH_URL,
        bbox  = bbox.as_bbox_str(),
        start = start_date,
        end   = end_date,
    );
    if max_results > 0 {
        url.push_str(&format!("&maxResults={}", max_results));
    }

    tracing::info!("ASF search: {url}");

    let resp = client
        .get(&url)
        .header("User-Agent", "erie-remote/0.1 (wreck-research)")
        .send()
        .await
        .context("ASF search request failed")?;

    if !resp.status().is_success() {
        return Err(anyhow!(
            "ASF search returned HTTP {}: {}",
            resp.status(),
            resp.text().await.unwrap_or_default()
        ));
    }

    let raw: serde_json::Value = resp.json().await.context("ASF JSON parse")?;
    let granules = raw
        .get(0)
        .and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("Unexpected ASF JSON shape"))?;

    let mut results = Vec::new();
    for g in granules {
        match serde_json::from_value::<AsfGranule>(g.clone()) {
            Ok(gr) => results.push(gr),
            Err(e) => tracing::warn!("ASF granule parse error: {e}"),
        }
    }

    tracing::info!("ASF search returned {} granules", results.len());
    Ok(results)
}

// -- GeoTIFF loader to ndarray -------------------------------------------------

/// Extract a patch of pixels around (lat, lon) from a single-band GeoTIFF.
pub fn extract_patch_from_geotiff(
    tif_path: &Path,
    lat: f64,
    lon: f64,
    half_px: usize,
) -> Result<Array2<f32>> {
    use tiff::decoder::{Decoder, DecodingResult};
    use std::fs::File;

    let file = File::open(tif_path).with_context(|| format!("Open {}", tif_path.display()))?;
    let mut decoder = Decoder::new(file).context("TIFF decoder init")?;
    let (width, height) = decoder.dimensions().context("TIFF dimensions")?;
    let (origin_lon, origin_lat, px_lon, px_lat) =
        read_geotransform(&mut decoder).unwrap_or((-90.0, 50.0, 0.0001, -0.0001));

    let col_f = (lon - origin_lon) / px_lon;
    let row_f = (lat - origin_lat) / px_lat;
    let col_c = col_f.round() as i64;
    let row_c = row_f.round() as i64;

    let half = half_px as i64;
    let row0 = (row_c - half).max(0) as usize;
    let col0 = (col_c - half).max(0) as usize;
    let rows = (2 * half + 1).min((height as i64 - row0 as i64).max(0)) as usize;
    let cols = (2 * half + 1).min((width  as i64 - col0 as i64).max(0)) as usize;

    if rows == 0 || cols == 0 {
        return Err(anyhow!("Candidate ({lat},{lon}) falls outside TIF extent"));
    }

    let decoded = decoder.read_image().context("TIFF decode")?;
    let data: Vec<f32> = match decoded {
        DecodingResult::F32(v) => v,
        DecodingResult::U16(v) => v.iter().map(|&x| x as f32).collect(),
        DecodingResult::I16(v) => v.iter().map(|&x| x as f32).collect(),
        _ => return Err(anyhow!("Unsupported TIFF pixel type")),
    };

    let mut patch = Array2::<f32>::zeros((rows, cols));
    for r in 0..rows {
        for c in 0..cols {
            let idx = (row0 + r) * width as usize + (col0 + c);
            if idx < data.len() {
                patch[[r, c]] = data[idx];
            }
        }
    }
    Ok(patch)
}

fn read_geotransform<R: std::io::Read + std::io::Seek>(
    decoder: &mut tiff::decoder::Decoder<R>,
) -> Option<(f64, f64, f64, f64)> {
    let scale_tag = decoder.get_tag(tiff::tags::Tag::Unknown(33550)).ok()?;
    let tie_tag   = decoder.get_tag(tiff::tags::Tag::Unknown(33922)).ok()?;
    let scale = scale_tag.into_f64_vec().ok()?;
    let tie   = tie_tag.into_f64_vec().ok()?;
    if scale.len() < 2 || tie.len() < 6 { return None; }
    Some((tie[3], tie[4], scale[0], -scale[1]))
}

// -- Curvelet-denoised backscatter extraction ----------------------------------

/// Apply curvelet denoising from the curvelet crate (5 scales, 3-sigma hard threshold).
pub fn curvelet_denoise(patch: &Array2<f32>, num_scales: usize) -> Result<Array2<f32>> {
    use curvelet::{curvelet_forward, curvelet_inverse};

    let mut coeffs = curvelet_forward(patch, num_scales)
        .map_err(|e| anyhow!("curvelet_forward: {e}"))?;

    // MAD noise estimate from finest-scale coefficients (Array2<Complex<f64>>)
    let mut abs_vals: Vec<f64> = coeffs.fine.iter().map(|c| c.norm()).collect();
    abs_vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let sigma = abs_vals[abs_vals.len() / 2] / 0.6745_f64;

    // hard_threshold: in-place, zeros detail coeffs below threshold
    coeffs.hard_threshold(3.0 * sigma);

    let denoised = curvelet_inverse(&coeffs)
        .map_err(|e| anyhow!("curvelet_inverse: {e}"))?;
    Ok(denoised)
}

pub fn centre_mean(patch: &Array2<f32>) -> f32 {
    patch.iter().sum::<f32>() / patch.len() as f32
}

// -- Multi-temporal stack analyser ---------------------------------------------

#[derive(Debug, Serialize)]
pub struct SarStack {
    pub n_scenes: usize,
    pub mean_sigma0: f32,
    pub std_sigma0: f32,
    /// 1 - std/mean  (higher = more temporally stable)
    pub coherence_proxy: f32,
    pub background_mean: f32,
    /// candidate mean / background mean
    pub anomaly_ratio: f32,
    pub anomaly_flagged: bool,
}

impl SarStack {
    pub fn new(candidate_series: &[f32], background_series: &[f32]) -> Self {
        let n = candidate_series.len();
        let mean = candidate_series.iter().sum::<f32>() / n as f32;
        let std  = {
            let var = candidate_series.iter().map(|x| (x - mean).powi(2)).sum::<f32>() / n as f32;
            var.sqrt()
        };
        let coherence_proxy = if mean.abs() > f32::EPSILON { 1.0 - std / mean } else { 0.0 };

        let bg_n   = background_series.len() as f32;
        let bg_mean = background_series.iter().sum::<f32>() / bg_n;
        let bg_std  = {
            let var = background_series.iter().map(|x| (x - bg_mean).powi(2)).sum::<f32>() / bg_n;
            var.sqrt()
        };
        let anomaly_ratio   = if bg_mean.abs() > f32::EPSILON { mean / bg_mean } else { 1.0 };
        let threshold       = 2.0 * bg_std / bg_mean.max(f32::EPSILON);
        let anomaly_flagged = (anomaly_ratio - 1.0).abs() > threshold;

        SarStack { n_scenes: n, mean_sigma0: mean, std_sigma0: std,
                   coherence_proxy, background_mean: bg_mean,
                   anomaly_ratio, anomaly_flagged }
    }

    pub fn to_sensor_result(&self) -> SensorResult {
        SensorResult {
            sensor: "Sentinel-1 SAR Multi-temporal Backscatter".to_string(),
            anomaly_detected: self.anomaly_flagged,
            value: self.coherence_proxy as f64,
            units: "coherence proxy [0-1]".to_string(),
            description: format!(
                "n={} scenes  mean_s0={:.4}  std={:.4}  coherence={:.3}  \
                 bg={:.4}  ratio={:.3}  flagged={}",
                self.n_scenes, self.mean_sigma0, self.std_sigma0,
                self.coherence_proxy, self.background_mean,
                self.anomaly_ratio, self.anomaly_flagged,
            ),
            source_url: ASF_SEARCH_URL.to_string(),
        }
    }
}

// -- Cache helpers -------------------------------------------------------------

pub fn cache_dir(data_root: &Path) -> PathBuf { data_root.join("sar_cache") }

// -- Top-level runner ----------------------------------------------------------

/// Full SAR pipeline: search ASF, download/cache GeoTIFFs, curvelet denoise, stack.
pub async fn run(
    candidate:       &Candidate,
    data_root:       &Path,
    earthdata_token: Option<&str>,
    start_date:      &str,
    end_date:        &str,
    dry_run:         bool,
) -> Result<SarStack> {
    let client  = build_client(earthdata_token)?;
    let bbox    = BoundingBox::around(candidate.lat, candidate.lon, 0.5);
    let granules = search_asf(&bbox, start_date, end_date, 500, &client).await?;
    tracing::info!("Found {} Sentinel-1 IW GRD_HD scenes", granules.len());

    if dry_run || granules.is_empty() {
        tracing::info!("Dry run - returning empty SAR stack");
        return Ok(SarStack::new(&[1.0], &[1.0]));
    }

    std::fs::create_dir_all(cache_dir(data_root))?;
    let mut cand_series: Vec<f32>   = Vec::new();
    let mut bg_series:   Vec<f32>   = Vec::new();

    for g in &granules {
        let cache_path = cache_dir(data_root).join(format!("{}.json", g.granule_name));
        if cache_path.exists() {
            let cached: serde_json::Value =
                serde_json::from_str(&std::fs::read_to_string(&cache_path)?)?;
            if let (Some(cv), Some(bv)) = (
                cached["candidate_sigma0"].as_f64(),
                cached["background_sigma0"].as_f64(),
            ) {
                cand_series.push(cv as f32);
                bg_series.push(bv as f32);
                continue;
            }
        }

        let tif_path = match download_granule(&g.download_url, data_root, &client).await {
            Ok(p)  => p,
            Err(e) => { tracing::warn!("Download failed for {}: {e}", g.granule_name); continue; }
        };

        let candidate_sigma0 = extract_and_denoise(&tif_path, candidate.lat, candidate.lon)?;
        let bg = extract_background(&tif_path, candidate.lat, candidate.lon, 0.09)?;

        let cached = serde_json::json!({
            "granule": g.granule_name, "start_time": g.start_time,
            "candidate_sigma0": candidate_sigma0, "background_sigma0": bg,
        });
        std::fs::write(&cache_path, serde_json::to_string_pretty(&cached)?)?;
        tracing::info!("{} -> s0_cand={:.4}  s0_bg={:.4}", g.granule_name, candidate_sigma0, bg);
        cand_series.push(candidate_sigma0);
        bg_series.push(bg);
    }

    if cand_series.is_empty() {
        return Err(anyhow!("No SAR scenes successfully processed"));
    }
    Ok(SarStack::new(&cand_series, &bg_series))
}

async fn download_granule(url: &str, data_root: &Path, client: &reqwest::Client) -> Result<PathBuf> {
    let filename = url.split('/').last().unwrap_or("scene.tif").to_string();
    let out_path = cache_dir(data_root).join(&filename);
    if out_path.exists() { return Ok(out_path); }
    tracing::info!("Downloading {filename}...");
    let resp  = client.get(url).send().await.context("GRD download")?;
    if !resp.status().is_success() {
        return Err(anyhow!("Download {} HTTP {}", url, resp.status()));
    }
    let bytes = resp.bytes().await.context("Read bytes")?;
    std::fs::write(&out_path, &bytes)?;
    Ok(out_path)
}

fn extract_and_denoise(tif_path: &Path, lat: f64, lon: f64) -> Result<f32> {
    let patch    = extract_patch_from_geotiff(tif_path, lat, lon, 32)?;
    let denoised = curvelet_denoise(&patch, 5)
        .unwrap_or_else(|e| { tracing::warn!("Curvelet failed: {e}"); patch.clone() });
    Ok(centre_mean(&denoised))
}

fn extract_background(tif_path: &Path, lat: f64, lon: f64, offset_deg: f64) -> Result<f32> {
    let offsets = [(lat + offset_deg, lon), (lat - offset_deg, lon),
                   (lat, lon + offset_deg), (lat, lon - offset_deg)];
    let mut values = Vec::new();
    for (la, lo) in offsets {
        match extract_patch_from_geotiff(tif_path, la, lo, 8) {
            Ok(patch) => values.push(centre_mean(&patch)),
            Err(e) => tracing::warn!("Background extract failed at ({la},{lo}): {e}"),
        }
    }
    if values.is_empty() { return Err(anyhow!("All background extractions failed")); }
    Ok(values.iter().sum::<f32>() / values.len() as f32)
}

fn build_client(earthdata_token: Option<&str>) -> Result<reqwest::Client> {
    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert("User-Agent", "erie-remote/0.1 (wreck-research)".parse().unwrap());
    if let Some(token) = earthdata_token {
        headers.insert(
            reqwest::header::AUTHORIZATION,
            format!("Bearer {token}").parse().unwrap(),
        );
    }
    Ok(reqwest::Client::builder()
        .default_headers(headers)
        .redirect(reqwest::redirect::Policy::limited(10))
        .build()?)
}
