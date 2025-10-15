#!/usr/bin/env python3
"""
Enhanced BAG File Analysis GUI
Combines wreck detection review, BAG reconstruction, and visualization capabilities
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import subprocess
import threading
import json
from pathlib import Path
from datetime import datetime
import webbrowser

class EnhancedBAGAnalysisGUI:
    """Enhanced GUI with wreck detection, reconstruction, and visualization"""

    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced BAG File Analysis System")
        self.root.geometry("1600x900")

        # Data storage
        self.reconstruction_thread = None
        self.visualization_thread = None

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Setup the main GUI layout with multiple tabs"""

        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: PDF Analysis
        pdf_tab = ttk.Frame(notebook)
        notebook.add(pdf_tab, text="📄 PDF Analysis")
        self.setup_pdf_tab(pdf_tab)

        # Tab 2: BAG Reconstruction
        reconstruction_tab = ttk.Frame(notebook)
        notebook.add(reconstruction_tab, text="🚀 BAG Reconstruction")
        self.setup_reconstruction_tab(reconstruction_tab)

        # Tab 2: Visualization Gallery
        visualization_tab = ttk.Frame(notebook)
        notebook.add(visualization_tab, text="🖼️ Visualization Gallery")
        self.setup_visualization_tab(visualization_tab)

        # Tab 3: Results Viewer
        results_tab = ttk.Frame(notebook)
        notebook.add(results_tab, text="📊 Results Viewer")
        self.setup_results_tab(results_tab)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))

    def setup_pdf_tab(self, parent):
        """Setup the PDF analysis tab"""

        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="PDF Redaction Breaking & Analysis",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Description
        desc_text = """
        Break PDF redactions and extract hidden content using multiple advanced techniques.

        Features:
        • 🔍 Multi-layer redaction detection and removal
        • 🖼️ Image extraction and analysis from PDFs
        • 📝 Text recovery from redacted areas
        • 🔬 Pattern recognition and content reconstruction
        • 📊 Detailed analysis reports and visualizations
        """
        desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="PDF Analysis Controls")
        control_frame.pack(fill=tk.X, pady=(0, 20))

        # File/Directory selection
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(file_frame, text="PDF Source:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pdf_source_var = tk.StringVar(value="")
        ttk.Entry(file_frame, textvariable=self.pdf_source_var, width=50).grid(row=0, column=1, padx=(10, 5), pady=5)

        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=0, column=2, padx=(5, 0), pady=5)

        ttk.Button(button_frame, text="📄 Select PDF",
                  command=self.select_pdf_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="📁 Select Directory",
                  command=self.select_pdf_directory).pack(side=tk.LEFT)

        # Analysis options
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.deep_analysis_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Deep analysis (slower but more thorough)",
                       variable=self.deep_analysis_var).pack(anchor=tk.W)

        self.extract_images_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Extract and analyze images",
                       variable=self.extract_images_var).pack(anchor=tk.W)

        self.reconstruct_text_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Attempt text reconstruction",
                       variable=self.reconstruct_text_var).pack(anchor=tk.W)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(action_frame, text="🔍 Analyze PDF",
                  command=self.analyze_pdf).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(action_frame, text="📊 View Last Results",
                  command=self.view_pdf_results).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(action_frame, text="🖼️ Open Image Gallery",
                  command=self.open_pdf_images).pack(side=tk.LEFT, padx=(0, 10))

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Analysis Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True)

        # Progress bar
        self.pdf_progress_var = tk.DoubleVar()
        self.pdf_progress_bar = ttk.Progressbar(progress_frame, variable=self.pdf_progress_var,
                                               maximum=100, mode='determinate')
        self.pdf_progress_bar.pack(fill=tk.X, padx=10, pady=10)

        # Progress text
        self.pdf_status_text = tk.Text(progress_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.pdf_status_text.yview)
        self.pdf_status_text.configure(yscrollcommand=scrollbar.set)

        self.pdf_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=(0, 10))

    def setup_reconstruction_tab(self, parent):
        """Setup the BAG reconstruction tab"""

        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="Fast ML-Enhanced BAG Reconstruction",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Description
        desc_text = """
        Perform high-performance BAG file reconstruction using Rust acceleration and ML techniques.

        Features:
        • ⚡ 3.4x faster processing with Rust backend
        • 🤖 ML-based region prioritization and "jumping around"
        • 🔬 Advanced reconstruction techniques (pattern interpolation, geometric reconstruction)
        • 📊 Detailed performance metrics and confidence scoring
        """
        desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Reconstruction Controls")
        control_frame.pack(fill=tk.X, pady=(0, 20))

        # Directory selection
        dir_frame = ttk.Frame(control_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(dir_frame, text="BAG Files Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bag_dir_var = tk.StringVar(value="bagfiles")
        ttk.Entry(dir_frame, textvariable=self.bag_dir_var, width=50).grid(row=0, column=1, padx=(10, 5), pady=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_bag_directory).grid(row=0, column=2, padx=(5, 0), pady=5)

        # Reconstruction options
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.force_python_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Force Python fallback (disable Rust acceleration)",
                       variable=self.force_python_var).pack(anchor=tk.W)

        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(button_frame, text="🔍 Check Available Files",
                  command=self.check_available_files).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="🚀 Start Reconstruction",
                  command=self.start_reconstruction).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="📊 View Last Results",
                  command=self.view_last_results).pack(side=tk.LEFT, padx=(0, 10))

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Reconstruction Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True)

        # Progress bar
        self.recon_progress_var = tk.DoubleVar()
        self.recon_progress_bar = ttk.Progressbar(progress_frame, variable=self.recon_progress_var,
                                                 maximum=100, mode='determinate')
        self.recon_progress_bar.pack(fill=tk.X, padx=10, pady=10)

        # Progress text
        self.recon_status_text = tk.Text(progress_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.recon_status_text.yview)
        self.recon_status_text.configure(yscrollcommand=scrollbar.set)

        self.recon_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=(0, 10))

    def setup_visualization_tab(self, parent):
        """Setup the visualization gallery tab"""

        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="BAG Reconstruction Visualization Gallery",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Description
        desc_text = """
        View interactive visualizations of reconstructed BAG file areas.

        Features:
        • 🖼️ High-resolution bathymetry images
        • 🌈 Color-coded depth visualization
        • 📊 Performance metrics dashboard
        • 🔍 Detailed reconstruction analysis
        """
        desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Visualization Controls")
        control_frame.pack(fill=tk.X, pady=(0, 20))

        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="🎨 Generate Visualizations",
                  command=self.generate_visualizations).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="🌐 Open Gallery in Browser",
                  command=self.open_visualization_gallery).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="📁 Open Visualization Folder",
                  command=self.open_visualization_folder).pack(side=tk.LEFT, padx=(0, 10))

        # Gallery preview frame
        gallery_frame = ttk.LabelFrame(main_frame, text="Gallery Preview")
        gallery_frame.pack(fill=tk.BOTH, expand=True)

        # Gallery status
        self.gallery_status_var = tk.StringVar(value="No visualizations generated yet")
        ttk.Label(gallery_frame, textvariable=self.gallery_status_var).pack(pady=20)

        # File list
        list_frame = ttk.Frame(gallery_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        ttk.Label(list_frame, text="Available Visualizations:").pack(anchor=tk.W)

        # Listbox for visualization files
        self.viz_listbox = tk.Listbox(list_frame, height=10)
        viz_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.viz_listbox.yview)
        self.viz_listbox.configure(yscrollcommand=viz_scrollbar.set)

        self.viz_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        viz_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Refresh button
        ttk.Button(list_frame, text="🔄 Refresh List",
                  command=self.refresh_visualization_list).pack(pady=(10, 0))

    def setup_results_tab(self, parent):
        """Setup the results viewer tab"""

        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="Reconstruction Results Viewer",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Results Controls")
        control_frame.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="📂 Load Results JSON",
                  command=self.load_results_json).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="📊 Show Performance Summary",
                  command=self.show_performance_summary).pack(side=tk.LEFT, padx=(0, 10))

        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Results Display")
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(results_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

    def browse_bag_directory(self):
        """Browse for BAG files directory"""
        directory = filedialog.askdirectory(title="Select BAG Files Directory")
        if directory:
            self.bag_dir_var.set(directory)

    def check_available_files(self):
        """Check available BAG files for reconstruction"""
        bag_dir = Path(self.bag_dir_var.get())
        if not bag_dir.exists():
            messagebox.showerror("Error", f"Directory {bag_dir} does not exist")
            return

        corrected_dir = bag_dir / "corrected"
        if not corrected_dir.exists():
            messagebox.showerror("Error", f"Corrected directory {corrected_dir} does not exist")
            return

        bag_files = list(corrected_dir.glob("*.bag"))
        if not bag_files:
            messagebox.showinfo("No Files", "No corrected BAG files found for reconstruction")
            return

        file_list = "\n".join([f"- {f.name}" for f in bag_files])
        messagebox.showinfo("Available Files",
                          f"Found {len(bag_files)} corrected BAG files ready for reconstruction:\n\n{file_list}")

    def start_reconstruction(self):
        """Start the reconstruction process"""
        if self.reconstruction_thread and self.reconstruction_thread.is_alive():
            messagebox.showwarning("Warning", "Reconstruction already running")
            return

        bag_dir = self.bag_dir_var.get()
        force_python = self.force_python_var.get()

        # Start reconstruction in background thread
        self.reconstruction_thread = threading.Thread(
            target=self.run_reconstruction,
            args=(bag_dir, force_python)
        )
        self.reconstruction_thread.daemon = True
        self.reconstruction_thread.start()

    def run_reconstruction(self, bag_dir, force_python):
        """Run the reconstruction process"""
        try:
            self.update_recon_status("🚀 Starting fast ML-enhanced reconstruction...\n")

            # Change to development_and_tools directory
            os.chdir(r"c:\Temp\bagfilework\development_and_tools")

            # Set environment variable if forcing Python
            env = os.environ.copy()
            if force_python:
                env["FORCE_PYTHON_FALLBACK"] = "1"

            # Run the reconstruction script
            cmd = [sys.executable, "fast_ml_reconstructor.py"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1,
                universal_newlines=True
            )

            # Read output in real-time
            for line in iter(process.stdout.readline, ''):
                self.update_recon_status(line)

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                self.update_recon_status("\n✅ Reconstruction completed successfully!\n")
                self.recon_progress_var.set(100)
            else:
                self.update_recon_status(f"\n❌ Reconstruction failed with code {return_code}\n")

        except Exception as e:
            self.update_recon_status(f"\n❌ Error during reconstruction: {e}\n")

    def update_recon_status(self, text):
        """Update reconstruction status text"""
        self.recon_status_text.config(state=tk.NORMAL)
        self.recon_status_text.insert(tk.END, text)
        self.recon_status_text.see(tk.END)
        self.recon_status_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def view_last_results(self):
        """View the last reconstruction results"""
        results_dir = Path(r"c:\Temp\bagfilework\development_and_tools\bagfiles")
        results_files = list(results_dir.glob("fast_reconstruction_results_*.json"))

        if not results_files:
            messagebox.showinfo("No Results", "No reconstruction results found")
            return

        # Get the most recent results file
        latest_results = max(results_files, key=lambda x: x.stat().st_mtime)

        try:
            with open(latest_results, 'r') as f:
                results_data = json.load(f)

            # Format results for display
            results_text = f"Reconstruction Results: {latest_results.name}\n"
            results_text += "=" * 50 + "\n\n"

            results_text += f"Timestamp: {results_data.get('timestamp', 'Unknown')}\n"
            results_text += f"Method: {results_data.get('reconstruction_method', 'Unknown')}\n"
            results_text += f"Rust Acceleration: {'✅' if results_data.get('rust_acceleration_used') else '❌'}\n\n"

            perf = results_data.get('performance_comparison', {})
            results_text += "Performance Summary:\n"
            results_text += f"- Files Processed: {perf.get('total_files', 0)}\n"
            results_text += f"- Average Confidence: {perf.get('average_confidence', 0):.3f}\n"
            results_text += f"- Techniques Used: {', '.join(perf.get('techniques_used', []))}\n\n"

            results_text += "Individual File Results:\n"
            for result in results_data.get('results', []):
                results_text += f"- {result.get('file', 'Unknown')}: {result.get('method', 'Unknown')}\n"

            # Show in message box (truncated if too long)
            if len(results_text) > 2000:
                results_text = results_text[:2000] + "\n\n... (truncated)"

            messagebox.showinfo("Last Reconstruction Results", results_text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results: {e}")

    def generate_visualizations(self):
        """Generate visualization images and webpage"""
        if self.visualization_thread and self.visualization_thread.is_alive():
            messagebox.showwarning("Warning", "Visualization generation already running")
            return

        # Start visualization in background thread
        self.visualization_thread = threading.Thread(target=self.run_visualization_generation)
        self.visualization_thread.daemon = True
        self.visualization_thread.start()

    def run_visualization_generation(self):
        """Run the visualization generation process"""
        try:
            self.gallery_status_var.set("🎨 Generating visualizations...")

            # Change to development_and_tools directory
            os.chdir(r"c:\Temp\bagfilework\development_and_tools")

            # Run the visualization generator
            cmd = [sys.executable, "bag_visualization_generator.py"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.gallery_status_var.set("✅ Visualizations generated successfully!")
                self.refresh_visualization_list()
            else:
                self.gallery_status_var.set("❌ Visualization generation failed")
                messagebox.showerror("Error", f"Visualization failed:\n{result.stderr}")

        except Exception as e:
            self.gallery_status_var.set("❌ Error generating visualizations")
            messagebox.showerror("Error", f"Failed to generate visualizations: {e}")

    def open_visualization_gallery(self):
        """Open the visualization gallery in web browser"""
        gallery_path = Path(r"c:\Temp\bagfilework\development_and_tools\bagfiles\reconstruction_gallery.html")

        if gallery_path.exists():
            webbrowser.open(str(gallery_path))
        else:
            messagebox.showwarning("Warning", "Visualization gallery not found. Generate visualizations first.")

    def open_visualization_folder(self):
        """Open the visualization folder"""
        viz_dir = Path(r"c:\Temp\bagfilework\development_and_tools\bagfiles\visualization")

        if viz_dir.exists():
            os.startfile(str(viz_dir))
        else:
            messagebox.showwarning("Warning", "Visualization folder not found. Generate visualizations first.")

    def refresh_visualization_list(self):
        """Refresh the list of available visualizations"""
        self.viz_listbox.delete(0, tk.END)

        viz_dir = Path(r"c:\Temp\bagfilework\development_and_tools\bagfiles\visualization")

        if viz_dir.exists():
            viz_files = list(viz_dir.glob("*.png"))
            for viz_file in sorted(viz_files):
                self.viz_listbox.insert(tk.END, viz_file.name)

            if not viz_files:
                self.viz_listbox.insert(tk.END, "No visualization images found")
        else:
            self.viz_listbox.insert(tk.END, "Visualization directory not found")

    def load_results_json(self):
        """Load and display results from JSON file"""
        file_path = filedialog.askopenfilename(
            title="Select Results JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=r"c:\Temp\bagfilework\development_and_tools\bagfiles"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Format for display
            formatted_text = json.dumps(data, indent=2)

            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, formatted_text)
            self.results_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file: {e}")

    def show_performance_summary(self):
        """Show performance summary from last results"""
        results_dir = Path(r"c:\Temp\bagfilework\development_and_tools\bagfiles")
        results_files = list(results_dir.glob("fast_reconstruction_results_*.json"))

        if not results_files:
            messagebox.showinfo("No Results", "No reconstruction results found")
            return

        # Get the most recent results file
        latest_results = max(results_files, key=lambda x: x.stat().st_mtime)

        try:
            with open(latest_results, 'r') as f:
                data = json.load(f)

            perf = data.get('performance_comparison', {})

            summary = f"""
PERFORMANCE SUMMARY
===================

Files Processed: {perf.get('total_files', 0)}
Average Confidence: {perf.get('average_confidence', 0):.3f}
Rust Acceleration: {'✅ Enabled' if data.get('rust_acceleration_used') else '❌ Disabled'}

Techniques Used:
{chr(10).join(f"• {tech}" for tech in perf.get('techniques_used', []))}

Performance Metrics:
{chr(10).join(f"• {k}: {v}" for k, v in perf.get('performance_metrics', {}).items())}
"""

            messagebox.showinfo("Performance Summary", summary)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load performance data: {e}")

    def select_pdf_file(self):
        """Select a single PDF file for analysis"""
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.pdf_source_var.set(file_path)

    def select_pdf_directory(self):
        """Select a directory containing PDF files"""
        directory = filedialog.askdirectory(title="Select PDF Directory")
        if directory:
            self.pdf_source_var.set(directory)

    def analyze_pdf(self):
        """Start PDF analysis process"""
        pdf_source = self.pdf_source_var.get()
        if not pdf_source:
            messagebox.showwarning("Warning", "Please select a PDF file or directory first")
            return

        # Check if source exists
        if os.path.isfile(pdf_source):
            if not pdf_source.lower().endswith('.pdf'):
                messagebox.showerror("Error", "Selected file is not a PDF")
                return
        elif os.path.isdir(pdf_source):
            pdf_files = [f for f in os.listdir(pdf_source) if f.lower().endswith('.pdf')]
            if not pdf_files:
                messagebox.showerror("Error", "No PDF files found in selected directory")
                return
        else:
            messagebox.showerror("Error", "Selected path does not exist")
            return

        # Start analysis in background thread
        analysis_thread = threading.Thread(target=self.run_pdf_analysis, args=(pdf_source,))
        analysis_thread.daemon = True
        analysis_thread.start()

    def run_pdf_analysis(self, pdf_source):
        """Run the PDF analysis process"""
        try:
            self.update_pdf_status("🔍 Starting PDF analysis...\n")

            # Change to development_and_tools directory
            os.chdir(r"c:\Temp\bagfilework\development_and_tools")

            # Prepare command arguments
            cmd = [sys.executable, "unified_redaction_breaker.py"]

            # Add source
            if os.path.isfile(pdf_source):
                cmd.extend(["--file", pdf_source])
            else:
                cmd.extend(["--directory", pdf_source])

            # Add options
            if self.deep_analysis_var.get():
                cmd.append("--deep")
            if self.extract_images_var.get():
                cmd.append("--images")
            if self.reconstruct_text_var.get():
                cmd.append("--text")

            self.update_pdf_status(f"Running command: {' '.join(cmd)}\n\n")

            # Run the analysis
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output in real-time
            for line in iter(process.stdout.readline, ''):
                self.update_pdf_status(line)

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                self.update_pdf_status("\n✅ PDF analysis completed successfully!\n")
                self.pdf_progress_var.set(100)
            else:
                self.update_pdf_status(f"\n❌ PDF analysis failed with code {return_code}\n")

        except Exception as e:
            self.update_pdf_status(f"\n❌ Error during PDF analysis: {e}\n")

    def update_pdf_status(self, text):
        """Update PDF analysis status text"""
        self.pdf_status_text.config(state=tk.NORMAL)
        self.pdf_status_text.insert(tk.END, text)
        self.pdf_status_text.see(tk.END)
        self.pdf_status_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def view_pdf_results(self):
        """View the last PDF analysis results"""
        results_dir = Path(r"c:\Temp\bagfilework\development_and_tools")
        results_files = list(results_dir.glob("*redaction*results*.json")) + \
                       list(results_dir.glob("*analysis*results*.json"))

        if not results_files:
            messagebox.showinfo("No Results", "No PDF analysis results found")
            return

        # Get the most recent results file
        latest_results = max(results_files, key=lambda x: x.stat().st_mtime)

        try:
            with open(latest_results, 'r') as f:
                results_data = json.load(f)

            # Format results for display
            results_text = f"PDF Analysis Results: {latest_results.name}\n"
            results_text += "=" * 50 + "\n\n"

            if "total_files_analyzed" in results_data:
                results_text += f"Files Analyzed: {results_data['total_files_analyzed']}\n"
            if "successful_breakthroughs" in results_data:
                results_text += f"Successful Breakthroughs: {results_data['successful_breakthroughs']}\n"
            if "total_breakthroughs" in results_data:
                results_text += f"Total Breakthroughs: {results_data['total_breakthroughs']}\n"

            # Show techniques used
            if "techniques_attempted" in results_data:
                results_text += f"\nTechniques Used: {', '.join(results_data['techniques_attempted'])}\n"

            # Show file results
            if "file_results" in results_data:
                results_text += f"\nFile Results:\n"
                for file_result in results_data["file_results"][:5]:  # Show first 5
                    results_text += f"- {file_result.get('file', 'Unknown')}: {len(file_result.get('breakthroughs', []))} breakthroughs\n"

                if len(results_data["file_results"]) > 5:
                    results_text += f"... and {len(results_data['file_results']) - 5} more files\n"

            # Show in message box (truncated if too long)
            if len(results_text) > 2000:
                results_text = results_text[:2000] + "\n\n... (truncated)"

            messagebox.showinfo("PDF Analysis Results", results_text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF results: {e}")

    def open_pdf_images(self):
        """Open the PDF images gallery/folder"""
        images_dir = Path(r"c:\Temp\bagfilework\development_and_tools\pdf_images")

        if images_dir.exists():
            # Try to open in file explorer
            try:
                os.startfile(str(images_dir))
            except:
                # Fallback: show message
                messagebox.showinfo("PDF Images", f"PDF images are located in:\n{images_dir}")
        else:
            messagebox.showinfo("No Images", "No PDF images found. Run PDF analysis with image extraction first.")


def main():
    """Launch the enhanced GUI"""
    root = tk.Tk()
    app = EnhancedBAGAnalysisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()