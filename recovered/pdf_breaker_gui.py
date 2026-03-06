import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def create_pdf_breaker_tab(parent):
    frame = ttk.Frame(parent)

    ttk.Label(frame, text="PDF Breaker Tool", font=("Arial", 14, "bold")).pack(pady=10)

    row = ttk.Frame(frame)
    row.pack(fill="x", padx=20, pady=5)
    ttk.Label(row, text="PDF File:").pack(side="left")
    pdf_var = tk.StringVar()
    ttk.Entry(row, textvariable=pdf_var, width=55).pack(side="left", padx=5)

    def select_pdf():
        path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if path:
            pdf_var.set(path)

    def run_redaction_breaker():
        pdf_path = pdf_var.get().strip()
        if not pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return
        gui_script = REPO / "bag_processor" / "enhanced_bag_gui.py"
        if not gui_script.exists():
            messagebox.showerror("Error", f"Could not find enhanced_bag_gui.py at:\n{gui_script}")
            return
        subprocess.Popen([sys.executable, str(gui_script), pdf_path],
                         creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
        messagebox.showinfo("Launched", "PDF Redaction Breaker opened in a new window.")

    ttk.Button(row, text="Browse...", command=select_pdf).pack(side="left")
    ttk.Button(frame, text="Run Redaction Breaker", command=run_redaction_breaker).pack(pady=10)
    ttk.Label(frame, text="Launches the full PDF Analysis + Redaction Breaker tool.",
              foreground="gray").pack()

    return frame
