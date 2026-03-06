import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB_PATH = REPO / "db" / "wrecks.db"


def create_swayze_tab(parent):
    frame = ttk.Frame(parent)

    ttk.Label(frame, text="Swayze Database Tool", font=("Arial", 14, "bold")).pack(pady=10)

    search_row = ttk.Frame(frame)
    search_row.pack(fill="x", padx=20, pady=5)
    ttk.Label(search_row, text="Search:").pack(side="left")
    query_var = tk.StringVar()
    search_entry = ttk.Entry(search_row, textvariable=query_var, width=45)
    search_entry.pack(side="left", padx=5)

    results_text = scrolledtext.ScrolledText(frame, height=18, wrap="word", state="disabled")
    results_text.pack(fill="both", expand=True, padx=20, pady=5)

    def _show(text):
        results_text.config(state="normal")
        results_text.delete("1.0", "end")
        results_text.insert("end", text)
        results_text.config(state="disabled")

    def query_database():
        q = query_var.get().strip()
        if not DB_PATH.exists():
            messagebox.showerror("Error", f"Database not found:\n{DB_PATH}")
            return
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            if q:
                rows = conn.execute(
                    "SELECT name, lake, year_sunk, vessel_type, hull_material, lat, lon "
                    "FROM features WHERE name LIKE ? LIMIT 100",
                    (f"%{q}%",)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT name, lake, year_sunk, vessel_type, hull_material, lat, lon "
                    "FROM features LIMIT 100"
                ).fetchall()
            conn.close()
            if not rows:
                _show("No results found."); return
            lines = [f"{'Name':<40} {'Lake':<15} {'Year':>6}  {'Type':<20} {'Hull':<10}  Coords",
                     "-" * 110]
            for r in rows:
                lat = f"{r['lat']:.4f}" if r['lat'] else 'N/A'
                lon = f"{r['lon']:.4f}" if r['lon'] else 'N/A'
                lines.append(f"{(r['name'] or '')[:38]:<40} {(r['lake'] or '')[:14]:<15} "
                             f"{str(r['year_sunk'] or ''):>6}  {(r['vessel_type'] or '')[:18]:<20} "
                             f"{(r['hull_material'] or '')[:9]:<10}  {lat},{lon}")
            _show("\n".join(lines))
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def analyze_historical():
        if not DB_PATH.exists():
            messagebox.showerror("Error", f"Database not found:\n{DB_PATH}"); return
        try:
            conn = sqlite3.connect(str(DB_PATH))
            stats = {}
            for row in conn.execute("SELECT DISTINCT lake FROM features WHERE lake IS NOT NULL").fetchall():
                lk = row[0]
                n = conn.execute("SELECT COUNT(*) FROM features WHERE lake=?", (lk,)).fetchone()[0]
                steel = conn.execute("SELECT COUNT(*) FROM features WHERE lake=? AND hull_material='Steel'", (lk,)).fetchone()[0]
                coords = conn.execute("SELECT COUNT(*) FROM features WHERE lake=? AND lat IS NOT NULL", (lk,)).fetchone()[0]
                stats[lk] = (n, steel, coords)
            total = conn.execute("SELECT COUNT(*) FROM features").fetchone()[0]
            conn.close()
            lines = ["SWAYZE DATABASE HISTORICAL ANALYSIS", "=" * 50, f"Total wrecks: {total:,}", "",
                     f"{'Lake':<20} {'Total':>8}  {'Steel':>8}  {'Has Coords':>12}", "-" * 55]
            for lk, (n, steel, coords) in sorted(stats.items(), key=lambda x: -x[1][0]):
                lines.append(f"{lk:<20} {n:>8,}  {steel:>8,}  {coords:>12,}")
            _show("\n".join(lines))
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    search_entry.bind("<Return>", lambda e: query_database())
    btn_row = ttk.Frame(frame)
    btn_row.pack(pady=5)
    ttk.Button(btn_row, text="Query Database", command=query_database).pack(side="left", padx=5)
    ttk.Button(btn_row, text="Analyze Historical Data", command=analyze_historical).pack(side="left", padx=5)

    return frame
