"""NDBC Buoy Data Fetcher and Analog Storm Extractor.

Fetches NOAA NDBC buoy 45005 (Western Erie Basin) for confirmed analog storms.
Canadian buoys 45132 / 45142 are ECCC-hosted and not available on NDBC.

Analog storms:
  Elliott  Dec 23-24 2022  score=0.93 (BEST MATCH)
  Jan2024  Jan 13-14 2024  score=0.78
  Sandy    Oct 30-31 2012  score=-0.40 (counter-example)

NOTE: Elliott storm (Dec 23-24 2022) — buoy 45005 was pulled for winter lay-up
on Dec 15 2022, 8 days before the storm. No buoy data is available for Elliott.
Use CO-OPS Toledo/Buffalo seiche data as the primary instrument record.
All other storm phase parameters for Elliott are from NWS post-storm analysis.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
import urllib.request
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from historical_drift import StormPhase  # noqa: E402

CACHE_DIR = REPO / "magnetic_data" / "buoy_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BUOYS = {
    "45005": {"name": "Western Erie Basin (seiche/drawdown)",
              "lat": 41.67, "lon": -82.40, "source": "ndbc"},
    "45132": {"name": "Port Stanley (Central-East Erie, Canadian)",
              "lat": 42.49, "lon": -81.72, "source": "eccc",
              "eccc_note": "Canadian ECCC buoy. Not on NDBC."},
    "45142": {"name": "Central Lake Erie (Canadian)",
              "lat": 42.16, "lon": -81.28, "source": "eccc",
              "eccc_note": "Canadian ECCC buoy. Not on NDBC."},
}

NDBC_PRIMARY = "45005"

_NDBC_HIST = "https://www.ndbc.noaa.gov/data/historical/stdmet/{buoy}h{year}.txt.gz"
_NDBC_REALTIME = "https://www.ndbc.noaa.gov/data/realtime2/{buoy}.txt"
# Great Lakes: IGLD datum, hourly_height product
_COOPS_WL = (
    "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    "?begin_date={start}&end_date={end}&station={station}"
    "&product=hourly_height&datum=IGLD&time_zone=gmt&units=english&format=json"
)
COOPS_STATIONS = {"toledo": "9063053", "buffalo": "9014070"}

ANALOG_STORMS = {
    "elliott": {
        "label": "Elliott (Bomb Cyclone) Dec 23-24 2022",
        "best_match_reason": (
            "Near-perfect 1909 pattern match. SW winds 50+ mph shifting to NW hurricane force. "
            "15-22 ft waves central basin. 7 ft Toledo drop / 11 ft Buffalo surge = NW "
            "surface-current push toward PA/NY shore, identical to 1909 debris field."
        ),
        "similarity_score": 0.93,
        "buoys": ["45005"],
        "eccc_buoys": ["45132", "45142"],
        "windows": [(2022, 12, 23, 24)],
        "target_buoy": "45005",
        "seiche_notes": "Toledo -7.0 ft / Buffalo +10.8 ft (NOAA CO-OPS IGLD)",
        "coops_window": {"start": "20221221", "end": "20221226"},
        "buoy_note": "45005 pulled Dec 15 2022 (winter lay-up, 8 days before storm). "
                     "No buoy data. Use CO-OPS seiche + NWS post-storm analysis.",
    },
    "jan2024": {
        "label": "January 13-14 2024 Winter Storm",
        "best_match_reason": (
            "65+ mph SW winds. Lake-bed exposed Put-in-Bay (matching Dec 1909 low-water reports)."
        ),
        "similarity_score": 0.78,
        "buoys": ["45005"],
        "eccc_buoys": ["45132", "45142"],
        "windows": [(2024, 1, 13, 14)],
        "target_buoy": "45005",
        "seiche_notes": "Put-in-Bay lake-bed exposed; Buffalo surge ~6 ft",
        "coops_window": {"start": "20240111", "end": "20240116"},
        "buoy_note": "45005 not deployed Jan 2024 (winter lay-up). Use CO-OPS data.",
    },
    "sandy": {
        "label": "Superstorm Sandy Oct 30-31 2012",
        "best_match_reason": (
            "NE/N winds (counter-example). Debris goes SW, opposite of 1909. "
            "Confirms 1909 forcing was NW, not NE."
        ),
        "similarity_score": -0.40,
        "buoys": ["45005"],
        "eccc_buoys": ["45132", "45142"],
        "windows": [(2012, 10, 30, 31)],
        "target_buoy": "45005",
        "seiche_notes": "Reverse seiche: Buffalo drop / Toledo rise",
        "coops_window": {"start": "20121028", "end": "20121102"},
        "buoy_note": "45005 deployed Oct 2012 — buoy data available.",
    },
}

_FILL = {999, 9999, 99.0, 999.0, 9999.0}

def _is_fill(v):
    try:
        f = float(v)
        return f in _FILL or f >= 999
    except Exception:
        return True


def parse_ndbc_stdmet(raw_text, year, month, day_start, day_end):
    rows = []
    header = None
    for line in raw_text.splitlines():
        if line.startswith("#YY") or line.startswith("YY"):
            header = line.lstrip("#").split(); continue
        if line.startswith("#") or header is None: continue
        parts = line.split()
        if len(parts) < 5: continue
        try:
            yy, mm, dd, hh = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            if yy < 100: yy += 1900 if yy > 50 else 2000
        except Exception: continue
        if yy != year or mm != month: continue
        if not (day_start <= dd <= day_end): continue
        rec = {"timestamp": f"{yy:04d}-{mm:02d}-{dd:02d}T{hh:02d}:00:00Z"}
        for col, val in zip(header[5:], parts[5:]):
            if not _is_fill(val): rec[col] = float(val)
        rows.append(rec)
    return rows


def _fetch_gz(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BagrecoveryResearch/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return gzip.decompress(r.read()).decode("ascii", errors="replace")
    except Exception:
        return None


def _fetch_plain(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BagrecoveryResearch/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("ascii", errors="replace")
    except Exception:
        return None


def fetch_buoy_storm(buoy_id, year, month, day_start, day_end, force=False):
    key = f"{buoy_id}_{year}{month:02d}{day_start:02d}-{day_end:02d}.json"
    cache_path = CACHE_DIR / key
    if cache_path.exists() and not force:
        return json.loads(cache_path.read_text())
    text = _fetch_gz(_NDBC_HIST.format(buoy=buoy_id.lower(), year=year))
    if text is None:
        text = _fetch_plain(_NDBC_REALTIME.format(buoy=buoy_id.upper()))
    if text is None:
        print(f"  WARNING: Could not fetch buoy {buoy_id} for {year}")
        return []
    records = parse_ndbc_stdmet(text, year, month, day_start, day_end)
    cache_path.write_text(json.dumps(records, indent=2))
    print(f"  Cached {len(records)} records -> {cache_path.name}")
    return records


def fetch_coops_water_level(station, start_yyyymmdd, end_yyyymmdd, force=False):
    key = f"coops_{station}_{start_yyyymmdd}_{end_yyyymmdd}.json"
    cache_path = CACHE_DIR / key
    if cache_path.exists() and not force:
        return json.loads(cache_path.read_text())
    url = _COOPS_WL.format(start=start_yyyymmdd, end=end_yyyymmdd, station=station)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BagrecoveryResearch/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        if "data" not in data:
            print(f"  CO-OPS no data for {station}: {data.get('error', '')}")
            return []
        records = [{"t": x["t"], "v": float(x["v"])} for x in data["data"]]
        cache_path.write_text(json.dumps(records, indent=2))
        print(f"  CO-OPS {station}: {len(records)} records cached")
        return records
    except Exception as e:
        print(f"  CO-OPS fetch error {station}: {e}")
        return []


MS_TO_MPH = 2.23694
M_TO_FT = 3.28084


def records_to_phases(records, storm_label, phase_width_hours=3):
    if not records: return []
    records = sorted(records, key=lambda r: r["timestamp"])
    def _parse_ts(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    t0 = _parse_ts(records[0]["timestamp"])
    phases, block = [], []

    def _flush(blk, idx):
        if not blk: return None
        wspds = [r["WSPD"] * MS_TO_MPH for r in blk if "WSPD" in r]
        wdirs = [r["WDIR"] for r in blk if "WDIR" in r]
        wvhts = [r["WVHT"] * M_TO_FT for r in blk if "WVHT" in r]
        if not wspds: return None
        ws = sorted(wspds)[len(wspds)//2]
        wh = max(wvhts) if wvhts else 0.0
        if wdirs:
            sins = [math.sin(math.radians(d)) for d in wdirs]
            coss = [math.cos(math.radians(d)) for d in wdirs]
            wd = (math.degrees(math.atan2(sum(sins)/len(sins), sum(coss)/len(coss))) + 360) % 360
        else:
            wd = 270.0
        label = f"{storm_label} ph{idx+1} [{blk[0]['timestamp'][:10]} {blk[-1]['timestamp'][11:16]}]"
        return StormPhase(label=label, wind_speed_mph=round(ws,1), wind_dir_deg=round(wd,1),
                          dt_hours=float(phase_width_hours), wave_ht_ft=round(wh,1),
                          current_speed_kt=0.0, current_dir_deg=0.0)

    for rec in records:
        t = _parse_ts(rec["timestamp"])
        elapsed_h = (t - t0).total_seconds() / 3600
        expected_block = int(elapsed_h // phase_width_hours)
        if expected_block > len(phases):
            ph = _flush(block, len(phases))
            if ph: phases.append(ph)
            block = []
        block.append(rec)
    if block:
        ph = _flush(block, len(phases))
        if ph: phases.append(ph)
    return phases


def score_analog_similarity(analog_phases, target_phases):
    if not analog_phases or not target_phases:
        return {"score": 0.0, "details": "No data"}
    a_peak = max(p.wind_speed_mph for p in analog_phases)
    t_peak = max(p.wind_speed_mph for p in target_phases)
    speed_ratio = min(a_peak, t_peak) / max(a_peak, t_peak)
    a_dirs = [p.wind_dir_deg for p in analog_phases]
    starts_sw = 200 <= a_dirs[0] <= 310
    shifts_nw = any(280 <= d <= 340 for d in a_dirs)
    direction_match = 1.0 if (starts_sw and shifts_nw) else (0.5 if shifts_nw else 0.1)
    a_wave = max(p.wave_ht_ft for p in analog_phases)
    t_wave = max(p.wave_ht_ft for p in target_phases)
    wave_ratio = min(a_wave, t_wave) / max(a_wave, t_wave) if max(a_wave, t_wave) > 0 else 0.5
    composite = 0.4 * speed_ratio + 0.4 * direction_match + 0.2 * wave_ratio
    return {"score": round(composite, 3), "peak_wind_mph": round(a_peak, 1),
            "peak_wave_ft": round(a_wave, 1), "starts_sw": starts_sw,
            "shifts_nw": shifts_nw, "speed_ratio": round(speed_ratio, 3),
            "direction_match": round(direction_match, 3), "wave_ratio": round(wave_ratio, 3)}


def analyze_seiche(toledo_records, buffalo_records):
    if not toledo_records or not buffalo_records:
        return {"error": "No water level data"}
    t_vals = [r["v"] for r in toledo_records]
    b_vals = [r["v"] for r in buffalo_records]
    t_range = max(t_vals) - min(t_vals)
    b_range = max(b_vals) - min(b_vals)
    return {
        "toledo_drop_ft": round(t_range, 2),
        "buffalo_surge_ft": round(b_range, 2),
        "toledo_min_time_utc": toledo_records[t_vals.index(min(t_vals))]["t"],
        "buffalo_max_time_utc": buffalo_records[b_vals.index(max(b_vals))]["t"],
        "implied_current_direction": "E->W surface flow" if t_range > b_range else "W->E surface flow",
        "seiche_consistent_1909": t_range >= 4.0,
    }


def run_analog(storm_key, force=False):
    storm = ANALOG_STORMS.get(storm_key)
    if not storm:
        raise ValueError(f"Unknown storm: {storm_key}")
    print(f"\n{'='*60}\n  {storm['label']}\n{'='*60}")
    if storm.get("buoy_note"):
        print(f"  NOTE: {storm['buoy_note']}")

    all_phases = {}
    for buoy_id in storm["buoys"]:
        print(f"\n  Fetching buoy {buoy_id}...")
        all_records = []
        for year, month, d0, d1 in storm["windows"]:
            recs = fetch_buoy_storm(buoy_id, year, month, d0, d1, force=force)
            all_records.extend(recs)
        all_phases[buoy_id] = records_to_phases(all_records, f"{storm_key}_{buoy_id}")
        print(f"    -> {len(all_phases[buoy_id])} phases built")

    print("\n  Fetching CO-OPS water levels...")
    cw = storm.get("coops_window", {})
    toledo_wl = fetch_coops_water_level(COOPS_STATIONS["toledo"], cw["start"], cw["end"], force=force)
    buffalo_wl = fetch_coops_water_level(COOPS_STATIONS["buffalo"], cw["start"], cw["end"], force=force)
    seiche = analyze_seiche(toledo_wl, buffalo_wl)

    from historical_drift import MB2_CASE
    target_phases = MB2_CASE["storm_phases"][:3]
    primary_phases = all_phases.get(storm["target_buoy"], [])
    similarity = score_analog_similarity(primary_phases, target_phases)

    result = {
        "storm": storm_key, "label": storm["label"],
        "known_similarity": storm["similarity_score"],
        "computed_similarity": similarity, "seiche": seiche,
        "phases_by_buoy": {k: [asdict(p) for p in v] for k, v in all_phases.items()},
        "primary_phases": [asdict(p) for p in primary_phases],
        "buoy_note": storm.get("buoy_note", ""),
    }
    out_path = CACHE_DIR / f"{storm_key}_analysis.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"\n  Similarity score: {similarity['score']:.3f}")
    print(f"  Seiche Toledo: {seiche.get('toledo_drop_ft','?')} ft  Buffalo: {seiche.get('buffalo_surge_ft','?')} ft")
    print(f"  Analysis saved: {out_path.name}")
    return result


def load_cached_phases(storm_key, buoy_id=None):
    if storm_key not in ANALOG_STORMS: return []
    storm = ANALOG_STORMS[storm_key]
    target_buoy = buoy_id or storm["target_buoy"]
    cache = CACHE_DIR / f"{storm_key}_analysis.json"
    if not cache.exists(): return []
    data = json.loads(cache.read_text())
    raw = data.get("phases_by_buoy", {}).get(target_buoy, [])
    return [StormPhase(**p) for p in raw]


def list_cached():
    return [p.stem for p in CACHE_DIR.glob("*_analysis.json")]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="NDBC buoy analog storm fetcher")
    ap.add_argument("--storm", default="sandy")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--list-cached", action="store_true")
    args = ap.parse_args()
    if args.list_cached:
        print("Cached:", list_cached()); sys.exit(0)
    keys = list(ANALOG_STORMS) if args.storm == "all" else [k.strip() for k in args.storm.split(",")]
    results = {}
    for k in keys:
        results[k] = run_analog(k, force=args.fetch)
    if args.compare:
        print(f"\n{'Storm':<32} {'Score':>6}  {'SW->NW':>8}")
        for k, r in results.items():
            s = r["computed_similarity"]
            sw_nw = "YES" if s.get("starts_sw") and s.get("shifts_nw") else "NO"
            print(f"  {r['label'][:30]:<30}  {s['score']:>6.3f}  {sw_nw:>8}")
