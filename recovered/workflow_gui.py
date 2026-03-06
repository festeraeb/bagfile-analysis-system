import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def create_workflow_tab(parent):
    frame = ttk.Frame(parent)

    ttk.Label(frame, text="Full Detection Workflow", font=("Arial", 14, "bold")).pack(pady=10)
    info = (
        "Launches the Comprehensive BAG Analysis tool which runs the full pipeline:\n"
        "  - PDF redaction breaking\n"
        "  - BAG file reconstruction\n"
        "  - Anomaly detection & clustering\n"
        "  - KML / GeoJSON / PDF report export\n"
        "  - Swayze database integration\n"
    )
    ttk.Label(frame, text=info, justify="left").pack(padx=20, pady=5, anchor="w")

    output_row = ttk.Frame(frame)
    output_row.pack(fill="x", padx=20, pady=5)
    ttk.Label(output_row, text="Output Dir:").pack(side="left")
    out_var = tk.StringVar(value=str(REPO / "bagfilework" / "outputs"))
    ttk.Entry(output_row, textvariable=out_var, width=50).pack(side="left", padx=5)

    def browse_output():
        d = filedialog.askdirectory(title="Select Output Directory")
        if d:
            out_var.set(d)

    def run_full_workflow():
        gui_script = REPO / "bag_processor" / "comprehensive_bag_gui.py"
        if not gui_script.exists():
            messagebox.showerror("Error", f"Could not find comprehensive_bag_gui.py at:\n{gui_script}")
            return
        subprocess.Popen([sys.executable, str(gui_script)],
                         creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
        messagebox.showinfo("Launched", "Comprehensive workflow tool opened in a new window.")

    def view_results():
        import os
        out_dir = out_var.get().strip() or str(REPO / "bagfilework" / "outputs")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(out_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", out_dir])
        else:
            subprocess.Popen(["xdg-open", out_dir])

    ttk.Button(output_row, text="Browse...", command=browse_output).pack(side="left")
    btn_row = ttk.Frame(frame)
    btn_row.pack(pady=10)
    ttk.Button(btn_row, text="Run Full Workflow", command=run_full_workflow).pack(side="left", padx=5)
    ttk.Button(btn_row, text="View Results Folder", command=view_results).pack(side="left", padx=5)

    return frame
