use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;
use tracing_subscriber::EnvFilter;

use erie_remote::{candidate::CANDIDATE, goce, icesat2, sar};

#[derive(Parser)]
#[command(
    name    = "erie_remote",
    version = "0.1.0",
    about   = "Multi-physics remote-sensing cross-validation for Lake Erie deep-wreck detection",
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Directory for cached downloads and outputs
    #[arg(short, long, default_value = "erie_remote_data")]
    data_dir: PathBuf,

    /// NASA Earthdata Bearer token (SAR + ICESat-2 download)
    #[arg(long, env = "NASA_EARTHDATA_TOKEN")]
    earthdata_token: Option<String>,

    /// Skip all downloads; only process previously cached data
    #[arg(long, default_value_t = false)]
    dry_run: bool,

    /// Start date for data search (YYYY-MM-DD)
    #[arg(long, default_value = "2018-01-01")]
    start_date: String,

    /// End date for data search (YYYY-MM-DD)
    #[arg(long, default_value = "2025-12-31")]
    end_date: String,
}

#[derive(Subcommand)]
enum Commands {
    /// Sentinel-1 SAR multi-temporal backscatter analysis
    Sar,
    /// ICESat-2 ATL13 water surface elevation analysis
    Icesat2,
    /// GOCE/ICGEM free-air gravity analysis
    Goce,
    /// Run all three sensors and write combined_report.json
    All,
    /// Print candidate + physical detectability summary, then exit
    Info,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_env("RUST_LOG")
                .unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .compact()
        .init();

    std::fs::create_dir_all(&cli.data_dir)?;
    let cand  = &CANDIDATE;
    let token = cli.earthdata_token.as_deref();
    let dr    = cli.dry_run;
    let sd    = cli.start_date.as_str();
    let ed    = cli.end_date.as_str();
    let root  = &cli.data_dir;

    match cli.command {
        Commands::Info => { print_info(); }

        Commands::Sar => {
            let stack  = sar::run(cand, root, token, sd, ed, dr).await?;
            let result = stack.to_sensor_result();
            println!("\n=== SAR RESULT ===");
            println!("{}", result.description);
            println!("Anomaly flagged: {}", result.anomaly_detected);
            write_json(root, "sar_result.json", &serde_json::to_value(&stack)?)?;
        }

        Commands::Icesat2 => {
            let stack  = icesat2::run(cand, root, token, sd, ed, dr).await?;
            let result = stack.to_sensor_result();
            println!("\n=== ICESat-2 RESULT ===");
            println!("{}", result.description);
            println!("Anomaly flagged: {}", result.anomaly_detected);
            write_json(root, "icesat2_result.json", &serde_json::to_value(&stack)?)?;
        }

        Commands::Goce => {
            match goce::run(cand, root, dr).await {
                Ok(grav) => {
                    let result = grav.to_sensor_result();
                    println!("\n=== GOCE GRAVITY RESULT ===");
                    println!("{}", result.description);
                    println!("Azimuth concordant: {}", result.anomaly_detected);
                    write_json(root, "goce_result.json", &serde_json::to_value(&grav)?)?;
                }
                Err(e) => println!("GOCE run failed: {e}"),
            }
        }

        Commands::All => {
            println!("Running all three sensors for: {cand}");
            let sar_r = sar::run(cand, root, token, sd, ed, dr)
                .await.map(|s| s.to_sensor_result())
                .unwrap_or_else(|e| placeholder("Sentinel-1 SAR", &e.to_string()));
            let ice_r = icesat2::run(cand, root, token, sd, ed, dr)
                .await.map(|s| s.to_sensor_result())
                .unwrap_or_else(|e| placeholder("ICESat-2 ATL13", &e.to_string()));
            let goc_r = goce::run(cand, root, dr)
                .await.map(|g| g.to_sensor_result())
                .unwrap_or_else(|e| placeholder("GOCE/EIGEN-6C4", &e.to_string()));

            let results = [&sar_r, &ice_r, &goc_r];
            println!("\n{:=<62}", "");
            println!("  MULTI-PHYSICS CROSS-VALIDATION REPORT");
            println!("  Target: {cand}");
            println!("{:=<62}", "");
            let mut n_flagged = 0u32;
            for r in &results {
                let flag = if r.anomaly_detected { "[ANOMALY]" } else { "[clear  ]" };
                println!("  {flag}  {:<30}  {:.4} {}",
                    &r.sensor[..r.sensor.len().min(30)], r.value, r.units);
                if r.anomaly_detected { n_flagged += 1; }
            }
            println!("{:=<62}", "");
            println!("  Sensors flagged: {n_flagged}/3");
            println!("  0/3 no corroboration | 1/3 weak | 2/3 ROV warranted | 3/3 high priority");

            let report = serde_json::json!({
                "candidate": {"lat": cand.lat, "lon": cand.lon,
                               "amplitude_nt": cand.amplitude_nt, "label": cand.label},
                "sensors_flagged": n_flagged,
                "sensors": [
                    serde_json::to_value(sar_r)?,
                    serde_json::to_value(ice_r)?,
                    serde_json::to_value(goc_r)?,
                ],
            });
            write_json(root, "combined_report.json", &report)?;
            println!("\nFull report: {}", root.join("combined_report.json").display());
        }
    }
    Ok(())
}

fn write_json(root: &PathBuf, filename: &str, value: &serde_json::Value) -> anyhow::Result<()> {
    let path = root.join(filename);
    std::fs::write(&path, serde_json::to_string_pretty(value)?)?;
    tracing::info!("Wrote {}", path.display());
    Ok(())
}

fn print_info() {
    println!("{'='*62}");
    println!("  Erie Remote Sensing - detectability summary");
    println!("  Candidate: {CANDIDATE}");
    println!();
    println!("  SAR (Sentinel-1 C-band 5.6 cm):");
    println!("    Bragg resonance: capillary waves ~2.4 cm at 35deg incidence");
    println!("    Wreck thermal plume / current disruption -> ~0.3-0.8 dB anomaly");
    println!("    Curvelet denoising preserves 338-ft hull edge; N>30 scenes needed");
    println!();
    println!("  ICESat-2 ATL13 (532 nm green laser):");
    println!("    Secchi depth post-zebra-mussel: 8-12 m; Kd=0.1 -> 30 m penetration");
    println!("    Surface IQR anomaly, persistent >50% of monthly passes = flagged");
    println!("    Detectability: LOW. Useful as negative evidence.");
    println!();
    println!("  GOCE / EIGEN-6C4 gravity gradient:");
    println!("    Direct wreck: 0.35 uGal vs 1000 uGal noise floor -> undetectable");
    println!("    Valid use: gradient azimuth concordance with mag dipole strike");
    println!("    If grad_az ~= MAG_STRIKE (+/-30 deg): geological coincidence test");
    println!("  ROV survey is the only definitive confirmation method.");
}

fn placeholder(name: &str, err: &str) -> erie_remote::candidate::SensorResult {
    erie_remote::candidate::SensorResult {
        sensor: name.to_string(),
        anomaly_detected: false,
        value: 0.0,
        units: "".to_string(),
        description: format!("ERROR: {err}"),
        source_url: "".to_string(),
    }
}
