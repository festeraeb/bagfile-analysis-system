//! Erie Remote Sensing — multi-physics cross-validation pipeline
//!
//! # Science background
//!
//! The M&B No.2 candidate (42.4250°N, 80.8130°W) has a 305 nT magnetic anomaly
//! confirmed by multiple aeromag grids.  Three independent satellite observables
//! can EITHER confirm or refute the target as a high-density iron mass:
//!
//! ## 1. Sentinel-1 SAR backscatter coherence
//!
//! Sentinel-1 C-band (5.6 cm) measures sea-surface roughness via Bragg scattering.
//! Capillary waves with spacing ≈ λ/2 · sin(θ) ≈ 2.5 cm dominate the radar return.
//! A submarine structure (hull, debris field) can:
//!   - Generate a thermal micro-plume that locally damps capillary waves
//!     → persistent dark patch in VV backscatter
//!   - Create a near-bottom current disruption whose surface signature is
//!     phase-coherent across repeat passes (12-day orbit repeat)
//!     → elevated InSAR-like coherence in a multi-temporal stack
//!
//! We apply the Discrete Curvelet Transform (from the `curvelet` crate) to each
//! GRD scene before stacking.  Curvelets suppress Gaussian-noise speckle while
//! preserving curve-edge features — including the narrow linear anomaly you would
//! expect above a 338-ft steel hull aligned on a bearing.
//!
//! ## 2. ICESat-2 ATL13 water-surface elevation
//!
//! The ATLAS green photon lidar (532 nm) can penetrate 10–25 m of clear water.
//! Lake Erie Central Basin (~24 m at candidate) is borderline; post-zebra-mussel
//! transparency (Secchi depth 8–12 m since 2000) means some photons reach bottom.
//!
//! ATL13 provides water-surface height statistics per ~100 m segment.
//! A wreck protruding 1–3 m above the silt plane would appear as a persistent
//! narrow elevation spike that:
//!   - Does NOT move between passes (unlike seiches or waves)
//!   - Has a distinct shape vs wind-driven wave roughness
//!
//! We download all ATL13 passes over the Erie Central Basin, align them to a
//! 0.001° grid, compute the 10-year median surface, and flag cells more than
//! 2 × IQR above the local median as persistent anomalies.
//!
//! ## 3. GOCE gravity gradient (ICGEM EIGEN-6C4)
//!
//! The GOCE satellite (2009–2013) resolved gravity to ~80 km spatial resolution.
//! A 3,000-ton iron mass in 24 m of silt (density ≈ 1.8 g/cm³) displaces
//! ~1,667 m³ of lighter material, producing an upward Bouguer anomaly of roughly:
//!
//!   Δg ≈ 2π G Δρ h ≈ 2π × 6.674e-11 × 1200 × 24 ≈ 1.2 × 10⁻⁵ m/s²  (1.2 μGal)
//!
//! This is below GOCE's free-air sensitivity (~1 mGal).  However, if the wreck
//! sits in a tectonic lineament (Precambrian basement has measurable gravity relief
//! across the Erie basin), the GRAVITY GRADIENT DIRECTION can align with the
//! magnetic anomaly axis.  A bi-directional coincidence (mag + gravity same azimuth)
//! substantially reduces the probability of a geological false positive.
//!
//! We download a 1°×1° ICGEM free-air grid at 0.05° resolution, compute the
//! horizontal gravity gradient direction at the candidate, and compare to the
//! magnetic anomaly strike.

pub mod candidate;
pub mod sar;
pub mod icesat2;
pub mod goce;
