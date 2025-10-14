""""""

Wreck Detection Review GUIWreck Detection Review GUI

Interactive tool for reviewing and validating potential wreck detectionsInteractive tool for reviewing and validating potential wreck detections

""""""

from pathlib import Path

from tkinter import ttk, filedialog, messageboximport sys

from PIL import Image, ImageTkimport os

from matplotlib.backends.backend_tkagg import FigureCanvasTkAggfrom pathlib import Path

from rasterio.windows import Windowimport tkinter as tk

from pyproj import Transformerfrom tkinter import ttk, filedialog, messagebox

from datetime import datetimeimport pandas as pd

import numpy as np

from PIL import Image, ImageTk

class WreckDetectionReviewGUI:import matplotlib.pyplot as plt

    def __init__(self, root):from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.root = rootimport rasterio

        self.root.title("NOAA Wreck Detection Review Tool")from rasterio.windows import Window

        self.root.geometry("1600x900")from pyproj import Transformer

        import threading

        # Data storageimport queue

        self.results_df = Noneimport json

        self.current_index = 0import time

        self.bag_files_cache = {}from datetime import datetime

        self.annotations = {}  # Store user annotations

        

        # Live scan monitoringclass WreckDetectionReviewGUI:

        self.live_monitoring = False    def __init__(self, root):

        self.live_update_thread = None        self.root = root

        self.scan_process = None        self.root.title("NOAA Wreck Detection Review Tool")

        self.checkpoint_manager = None        self.root.geometry("1600x900")

                

        # Setup GUI        # Data storage

        self.setup_gui()        self.results_df = None

                self.current_index = 0

        # Start live monitoring if checkpoint exists        self.bag_files_cache = {}

        self.check_for_active_scan()        self.annotations = {}  # Store user annotations

                

    def setup_gui(self):        # Live scan monitoring

        """Setup the main GUI layout"""        self.live_monitoring = False

                self.live_update_thread = None

        # Create notebook for tabbed interface        self.scan_process = None

        notebook = ttk.Notebook(self.root)        self.checkpoint_manager = None

        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)        

                # Setup GUI

        # Tab 1: Detection Review        self.setup_gui()

        review_tab = ttk.Frame(notebook)        

        notebook.add(review_tab, text="Detection Review")        # Start live monitoring if checkpoint exists

        self.setup_review_tab(review_tab)        self.check_for_active_scan()

                

        # Tab 2: Live Scan Monitor    def setup_gui(self):

        monitor_tab = ttk.Frame(notebook)        """Setup the main GUI layout"""

        notebook.add(monitor_tab, text="Live Scan Monitor")        

        self.setup_monitor_tab(monitor_tab)        # Create notebook for tabbed interface

                notebook = ttk.Notebook(self.root)

        # Status bar        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.status_var = tk.StringVar(value="Ready")        

        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)        # Tab 1: Detection Review

        status_bar.pack(fill=tk.X, pady=(5, 0))        review_tab = ttk.Frame(notebook)

    def setup_review_tab(self, parent):        notebook.add(review_tab, text="Detection Review")

        """Setup the detection review tab"""        self.setup_review_tab(review_tab)

                

        # Main frame for this tab        # Tab 2: Live Scan Monitor

        main_frame = ttk.Frame(parent)        monitor_tab = ttk.Frame(notebook)

        main_frame.pack(fill=tk.BOTH, expand=True)        notebook.add(monitor_tab, text="Live Scan Monitor")

                self.setup_monitor_tab(monitor_tab)

        # Top frame for controls        

        control_frame = ttk.Frame(main_frame)        # Status bar

        control_frame.pack(fill=tk.X, pady=(0, 10))        self.status_var = tk.StringVar(value="Ready")

                status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)

        # Load results button        status_bar.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(control_frame, text="Load Scan Results",     def setup_review_tab(self, parent):

                  command=self.load_results).pack(side=tk.LEFT, padx=(0, 10))        """Setup the detection review tab"""

                

        # Navigation controls        # Main frame for this tab

        nav_frame = ttk.Frame(control_frame)        main_frame = ttk.Frame(parent)

        nav_frame.pack(side=tk.LEFT, padx=(10, 0))        main_frame.pack(fill=tk.BOTH, expand=True)

                

        ttk.Button(nav_frame, text=" Previous",         # Top frame for controls

                  command=self.previous_detection).pack(side=tk.LEFT, padx=(0, 5))        control_frame = ttk.Frame(main_frame)

                control_frame.pack(fill=tk.X, pady=(0, 10))

        self.index_label = ttk.Label(nav_frame, text="0 / 0")        

        self.index_label.pack(side=tk.LEFT, padx=(5, 5))        # Load results button

                ttk.Button(control_frame, text="Load Scan Results", 

        ttk.Button(nav_frame, text="Next ",                   command=self.load_results).pack(side=tk.LEFT, padx=(0, 10))

                  command=self.next_detection).pack(side=tk.LEFT, padx=(5, 0))        

                # Navigation controls

        # Filter controls        nav_frame = ttk.Frame(control_frame)

        filter_frame = ttk.Frame(control_frame)        nav_frame.pack(side=tk.LEFT, padx=(10, 0))

        filter_frame.pack(side=tk.RIGHT)        

                ttk.Button(nav_frame, text="◀ Previous", 

        ttk.Label(filter_frame, text="Min Anomaly Score:").pack(side=tk.LEFT)                  command=self.previous_detection).pack(side=tk.LEFT, padx=(0, 5))

        self.min_score_var = tk.DoubleVar(value=-0.1)        

        ttk.Scale(filter_frame, from_=-1.0, to=1.0, variable=self.min_score_var,        self.index_label = ttk.Label(nav_frame, text="0 / 0")

                 orient=tk.HORIZONTAL, length=150, command=self.apply_filters).pack(side=tk.LEFT, padx=(5, 10))        self.index_label.pack(side=tk.LEFT, padx=(5, 5))

                

        ttk.Button(filter_frame, text="Apply Filters",         ttk.Button(nav_frame, text="Next ▶", 

                  command=self.apply_filters).pack(side=tk.LEFT)                  command=self.next_detection).pack(side=tk.LEFT, padx=(5, 0))

                

        # Content frame (split left and right)        # Filter controls

        content_frame = ttk.Frame(main_frame)        filter_frame = ttk.Frame(control_frame)

        content_frame.pack(fill=tk.BOTH, expand=True)        filter_frame.pack(side=tk.RIGHT)

                

        # Left panel - Detection info and controls        ttk.Label(filter_frame, text="Min Anomaly Score:").pack(side=tk.LEFT)

        left_panel = ttk.Frame(content_frame, width=400)        self.min_score_var = tk.DoubleVar(value=-0.1)

        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))        ttk.Scale(filter_frame, from_=-1.0, to=1.0, variable=self.min_score_var,

        left_panel.pack_propagate(False)                 orient=tk.HORIZONTAL, length=150, command=self.apply_filters).pack(side=tk.LEFT, padx=(5, 10))

                

        # Detection info        ttk.Button(filter_frame, text="Apply Filters", 

        info_frame = ttk.LabelFrame(left_panel, text="Detection Information")                  command=self.apply_filters).pack(side=tk.LEFT)

        info_frame.pack(fill=tk.X, pady=(0, 10))        

                # Content frame (split left and right)

        self.info_text = tk.Text(info_frame, height=15, width=45, wrap=tk.WORD)        content_frame = ttk.Frame(main_frame)

        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)        content_frame.pack(fill=tk.BOTH, expand=True)

        self.info_text.configure(yscrollcommand=info_scrollbar.set)        

        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)        # Left panel - Detection info and controls

        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)        left_panel = ttk.Frame(content_frame, width=400)

                left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Annotation controls        left_panel.pack_propagate(False)

        annotation_frame = ttk.LabelFrame(left_panel, text="Classification")        

        annotation_frame.pack(fill=tk.X, pady=(0, 10))        # Detection info

                info_frame = ttk.LabelFrame(left_panel, text="Detection Information")

        self.classification_var = tk.StringVar(value="Unknown")        info_frame.pack(fill=tk.X, pady=(0, 10))

        classifications = ["Wreck - Confirmed", "Wreck - Likely", "Wreck - Possible",         

                          "False Positive", "Geological Feature", "Noise/Artifact", "Unknown"]        self.info_text = tk.Text(info_frame, height=15, width=45, wrap=tk.WORD)

                info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)

        for cls in classifications:        self.info_text.configure(yscrollcommand=info_scrollbar.set)

            pass  # omitted for brevity        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Confidence rating        

        conf_frame = ttk.Frame(annotation_frame)        # Annotation controls

        conf_frame.pack(fill=tk.X, pady=(5, 0))        annotation_frame = ttk.LabelFrame(left_panel, text="Classification")

        ttk.Label(conf_frame, text="Confidence:").pack(side=tk.LEFT)        annotation_frame.pack(fill=tk.X, pady=(0, 10))

                

        self.confidence_var = tk.IntVar(value=3)        self.classification_var = tk.StringVar(value="Unknown")

        ttk.Scale(conf_frame, from_=1, to=5, variable=self.confidence_var,        classifications = ["Wreck - Confirmed", "Wreck - Likely", "Wreck - Possible", 

                 orient=tk.HORIZONTAL, length=100, command=self.save_annotation).pack(side=tk.LEFT, padx=(5, 0))                          "False Positive", "Geological Feature", "Noise/Artifact", "Unknown"]

                

        # Notes        for cls in classifications:

        notes_frame = ttk.LabelFrame(left_panel, text="Notes")            ttk.Radiobutton(annotation_frame, text=cls, variable=self.classification_var,

        notes_frame.pack(fill=tk.BOTH, expand=True)                           value=cls, command=self.save_annotation).pack(anchor=tk.W)

                

        self.notes_text = tk.Text(notes_frame, height=5, wrap=tk.WORD)        # Confidence rating

        notes_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)        conf_frame = ttk.Frame(annotation_frame)

        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)        conf_frame.pack(fill=tk.X, pady=(5, 0))

        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)        ttk.Label(conf_frame, text="Confidence:").pack(side=tk.LEFT)

        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)        

                self.confidence_var = tk.IntVar(value=3)

        # Bind notes changes        ttk.Scale(conf_frame, from_=1, to=5, variable=self.confidence_var,

        self.notes_text.bind('<KeyRelease>', self.save_annotation)                 orient=tk.HORIZONTAL, length=100, command=self.save_annotation).pack(side=tk.LEFT, padx=(5, 0))

                

        # Right panel - Bathymetric visualization        # Notes

        right_panel = ttk.Frame(content_frame)        notes_frame = ttk.LabelFrame(left_panel, text="Notes")

        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)        notes_frame.pack(fill=tk.BOTH, expand=True)

                

        viz_frame = ttk.LabelFrame(right_panel, text="Bathymetric Data Visualization")        self.notes_text = tk.Text(notes_frame, height=5, wrap=tk.WORD)

        viz_frame.pack(fill=tk.BOTH, expand=True)        notes_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)

                self.notes_text.configure(yscrollcommand=notes_scrollbar.set)

        # Matplotlib figure        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)        

        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)        # Bind notes changes

            self.notes_text.bind('<KeyRelease>', self.save_annotation)

    def setup_monitor_tab(self, parent):        

        """Setup the live scan monitoring tab"""        # Right panel - Bathymetric visualization

                right_panel = ttk.Frame(content_frame)

        main_frame = ttk.Frame(parent)        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        main_frame.pack(fill=tk.BOTH, expand=True)        

                viz_frame = ttk.LabelFrame(right_panel, text="Bathymetric Data Visualization")

        # Control panel        viz_frame.pack(fill=tk.BOTH, expand=True)

        control_panel = ttk.LabelFrame(main_frame, text="Scan Control")        

        control_panel.pack(fill=tk.X, pady=(0, 10))        # Matplotlib figure

                self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))

        control_buttons = ttk.Frame(control_panel)        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)

        control_buttons.pack(fill=tk.X, padx=10, pady=5)        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            

        self.start_scan_btn = ttk.Button(control_buttons, text="f680 Start New Scan",     def setup_monitor_tab(self, parent):

                                        command=self.start_new_scan)        """Setup the live scan monitoring tab"""

        self.start_scan_btn.pack(side=tk.LEFT, padx=(0, 5))        

                main_frame = ttk.Frame(parent)

        self.pause_scan_btn = ttk.Button(control_buttons, text="3f8 Pause",         main_frame.pack(fill=tk.BOTH, expand=True)

                                        command=self.pause_scan, state=tk.DISABLED)        

        self.pause_scan_btn.pack(side=tk.LEFT, padx=(0, 5))        # Control panel

                control_panel = ttk.LabelFrame(main_frame, text="Scan Control")

        self.resume_scan_btn = ttk.Button(control_buttons, text=" 25b6 Resume",         control_panel.pack(fill=tk.X, pady=(0, 10))

                                         command=self.resume_scan, state=tk.DISABLED)        

        self.resume_scan_btn.pack(side=tk.LEFT, padx=(0, 5))        control_buttons = ttk.Frame(control_panel)

                control_buttons.pack(fill=tk.X, padx=10, pady=5)

        self.stop_scan_btn = ttk.Button(control_buttons, text="f6d1 Stop",         

                                       command=self.stop_scan, state=tk.DISABLED)        self.start_scan_btn = ttk.Button(control_buttons, text="🚀 Start New Scan", 

        self.stop_scan_btn.pack(side=tk.LEFT, padx=(0, 5))                                        command=self.start_new_scan)

                self.start_scan_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Resume existing scan        

        self.resume_existing_btn = ttk.Button(control_buttons, text="f501 Resume Existing",         self.pause_scan_btn = ttk.Button(control_buttons, text="⏸️ Pause", 

                                             command=self.resume_existing_scan)                                        command=self.pause_scan, state=tk.DISABLED)

        self.resume_existing_btn.pack(side=tk.LEFT, padx=(10, 0))        self.pause_scan_btn.pack(side=tk.LEFT, padx=(0, 5))

                

        # Progress section        self.resume_scan_btn = ttk.Button(control_buttons, text="▶️ Resume", 

        progress_frame = ttk.LabelFrame(main_frame, text="Scan Progress")                                         command=self.resume_scan, state=tk.DISABLED)

        progress_frame.pack(fill=tk.X, pady=(0, 10))        self.resume_scan_btn.pack(side=tk.LEFT, padx=(0, 5))

                

        # Overall progress        self.stop_scan_btn = ttk.Button(control_buttons, text="🛑 Stop", 

        ttk.Label(progress_frame, text="Overall Progress:").pack(anchor=tk.W, padx=10, pady=(5, 0))                                       command=self.stop_scan, state=tk.DISABLED)

        self.overall_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')        self.stop_scan_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.overall_progress.pack(fill=tk.X, padx=10, pady=5)        

                # Resume existing scan

        self.overall_progress_label = ttk.Label(progress_frame, text="0%")        self.resume_existing_btn = ttk.Button(control_buttons, text="🔄 Resume Existing", 

        self.overall_progress_label.pack(anchor=tk.W, padx=10)                                             command=self.resume_existing_scan)

                self.resume_existing_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Current file progress        

        ttk.Label(progress_frame, text="Current File:").pack(anchor=tk.W, padx=10, pady=(10, 0))        # Progress section

        self.current_file_label = ttk.Label(progress_frame, text="No file")        progress_frame = ttk.LabelFrame(main_frame, text="Scan Progress")

        self.current_file_label.pack(anchor=tk.W, padx=10)        progress_frame.pack(fill=tk.X, pady=(0, 10))

                

        self.file_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')        # Overall progress

        self.file_progress.pack(fill=tk.X, padx=10, pady=5)        ttk.Label(progress_frame, text="Overall Progress:").pack(anchor=tk.W, padx=10, pady=(5, 0))

                self.overall_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')

        self.file_progress_label = ttk.Label(progress_frame, text="0%")        self.overall_progress.pack(fill=tk.X, padx=10, pady=5)

        self.file_progress_label.pack(anchor=tk.W, padx=10)        

                self.overall_progress_label = ttk.Label(progress_frame, text="0%")

        # Statistics panel        self.overall_progress_label.pack(anchor=tk.W, padx=10)

        stats_frame = ttk.LabelFrame(main_frame, text="Live Statistics")        

        stats_frame.pack(fill=tk.X, pady=(0, 10))        # Current file progress

                ttk.Label(progress_frame, text="Current File:").pack(anchor=tk.W, padx=10, pady=(10, 0))

        stats_grid = ttk.Frame(stats_frame)        self.current_file_label = ttk.Label(progress_frame, text="No file")

        stats_grid.pack(fill=tk.X, padx=10, pady=5)        self.current_file_label.pack(anchor=tk.W, padx=10)

                

        # Create stat labels        self.file_progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')

        self.stat_labels = {}        self.file_progress.pack(fill=tk.X, padx=10, pady=5)

        stat_names = [        

            ("Total Detections", "total_detections"),        self.file_progress_label = ttk.Label(progress_frame, text="0%")

            ("Wreck Signatures", "wreck_detections"),        self.file_progress_label.pack(anchor=tk.W, padx=10)

            ("Obstruction Signatures", "obstruction_detections"),        

            ("Redaction Signatures", "redaction_detections"),        # Statistics panel

            ("Scan Time", "scan_time"),        stats_frame = ttk.LabelFrame(main_frame, text="Live Statistics")

            ("Est. Time Remaining", "eta")        stats_frame.pack(fill=tk.X, pady=(0, 10))

        ]        

                stats_grid = ttk.Frame(stats_frame)

        for i, (display_name, key) in enumerate(stat_names):        stats_grid.pack(fill=tk.X, padx=10, pady=5)

            pass  # omitted for brevity        

                # Create stat labels

        # Recent detections list        self.stat_labels = {}

        recent_frame = ttk.LabelFrame(main_frame, text="Recent Detections")        stat_names = [

        recent_frame.pack(fill=tk.BOTH, expand=True)            ("Total Detections", "total_detections"),

                    ("Wreck Signatures", "wreck_detections"),

        # Create treeview for recent detections            ("Obstruction Signatures", "obstruction_detections"),

        columns = ("Time", "Type", "Confidence", "Location")            ("Redaction Signatures", "redaction_detections"),

        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=10)            ("Scan Time", "scan_time"),

                    ("Est. Time Remaining", "eta")

        for col in columns:        ]

            pass  # omitted for brevity        

                for i, (display_name, key) in enumerate(stat_names):

        recent_scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_tree.yview)            row = i // 2

        self.recent_tree.configure(yscrollcommand=recent_scrollbar.set)            col = (i % 2) * 2

                    

        self.recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)            ttk.Label(stats_grid, text=f"{display_name}:").grid(row=row, column=col, sticky=tk.W, padx=(0, 5))

        recent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)            self.stat_labels[key] = ttk.Label(stats_grid, text="0", font=("Arial", 10, "bold"))

                    self.stat_labels[key].grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20))

    def load_results(self):        

        """Load scan results from CSV file"""        # Recent detections list

        file_path = filedialog.askopenfilename(        recent_frame = ttk.LabelFrame(main_frame, text="Recent Detections")

            title="Select Scan Results File",        recent_frame.pack(fill=tk.BOTH, expand=True)

            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],        

            initialdir=r"c:\Temp\bagfilework\enhanced_scan_results"        # Create treeview for recent detections

        )        columns = ("Time", "Type", "Confidence", "Location")

                self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=10)

        if not file_path:        

            pass  # omitted for brevity        for col in columns:

                        self.recent_tree.heading(col, text=col)

        try:            self.recent_tree.column(col, width=120)

            pass  # omitted for brevity        

                        recent_scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_tree.yview)

        except Exception as e:        self.recent_tree.configure(yscrollcommand=recent_scrollbar.set)

            pass  # omitted for brevity        

            self.recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)

    def apply_filters(self, *args):        recent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

        """Apply filters to the results"""        

        if self.results_df is None:    def load_results(self):

            pass  # omitted for brevity        """Load scan results from CSV file"""

                    file_path = filedialog.askopenfilename(

        # Filter by minimum anomaly score            title="Select Scan Results File",

        min_score = self.min_score_var.get()            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],

        self.filtered_df = self.results_df[            initialdir=r"c:\Temp\bagfilework\enhanced_scan_results"

            self.results_df.get('anomaly_score', -999) >= min_score        )

        ].copy()        

                if not file_path:

        # Sort by anomaly score descending            return

        if 'anomaly_score' in self.filtered_df.columns:            

            pass  # omitted for brevity        try:

                    self.results_df = pd.read_csv(file_path)

        # Reset index and update display            self.status_var.set(f"Loaded {len(self.results_df)} detections")

        if len(self.filtered_df) > 0:            

            pass  # omitted for brevity            # Apply initial filters

                    self.apply_filters()

    def update_navigation(self):            

        """Update navigation label"""            if len(self.filtered_df) > 0:

        pass  # omitted for brevity                self.current_index = 0

                    self.display_detection()

    def previous_detection(self):            else:

        pass  # omitted for brevity                messagebox.showwarning("No Data", "No detections match the current filters")

                    

    def next_detection(self):        except Exception as e:

        pass  # omitted for brevity            messagebox.showerror("Error", f"Failed to load results: {str(e)}")

        

    def display_detection(self):    def apply_filters(self, *args):

        pass  # omitted for brevity        """Apply filters to the results"""

            if self.results_df is None:

    def update_info_panel(self, detection):            return

        pass  # omitted for brevity            

            # Filter by minimum anomaly score

    def update_visualization(self, detection):        min_score = self.min_score_var.get()

        pass  # omitted for brevity        self.filtered_df = self.results_df[

                self.results_df.get('anomaly_score', -999) >= min_score

    def find_bag_file(self, source_file):        ].copy()

        pass  # omitted for brevity        

            # Sort by anomaly score descending

    def extract_and_plot_bathymetry(self, bag_path, center_x, center_y, detection):        if 'anomaly_score' in self.filtered_df.columns:

        pass  # omitted for brevity            self.filtered_df = self.filtered_df.sort_values('anomaly_score', ascending=False)

            

    def plot_bathymetry(self, elevation, uncertainty, detection):        # Reset index and update display

        pass  # omitted for brevity        if len(self.filtered_df) > 0:

                self.current_index = min(self.current_index, len(self.filtered_df) - 1)

    def load_annotation(self, detection):            self.update_navigation()

        pass  # omitted for brevity            self.display_detection()

            

    def save_annotation(self, *args):    def update_navigation(self):

        pass  # omitted for brevity        """Update navigation label"""

            if self.filtered_df is not None and len(self.filtered_df) > 0:

    def save_annotations_to_file(self):            self.index_label.config(text=f"{self.current_index + 1} / {len(self.filtered_df)}")

        pass  # omitted for brevity        else:

            self.index_label.config(text="0 / 0")

    

def main():    def previous_detection(self):

    """Launch the GUI"""        """Go to previous detection"""

    root = tk.Tk()        if self.filtered_df is not None and len(self.filtered_df) > 0:

    app = WreckDetectionReviewGUI(root)            self.current_index = (self.current_index - 1) % len(self.filtered_df)

    root.mainloop()            self.display_detection()

    

    def next_detection(self):

if __name__ == "__main__":        """Go to next detection"""

    main()        if self.filtered_df is not None and len(self.filtered_df) > 0:

            self.current_index = (self.current_index + 1) % len(self.filtered_df)
            self.display_detection()
    
    def display_detection(self):
        """Display current detection information and visualization"""
        if self.filtered_df is None or len(self.filtered_df) == 0:
            return
            
        self.update_navigation()
        
        # Get current detection
        detection = self.filtered_df.iloc[self.current_index]
        
        # Update info panel
        self.update_info_panel(detection)
        
        # Load annotation if exists
        self.load_annotation(detection)
        
        # Update visualization in background thread
        self.status_var.set("Loading bathymetric data...")
        threading.Thread(target=self.update_visualization, args=(detection,), daemon=True).start()
    
    def update_info_panel(self, detection):
        """Update the information panel with detection details"""
        self.info_text.delete(1.0, tk.END)
        
        info_text = f"""DETECTION DETAILS
==================

Location:
  Latitude: {detection.get('center_lat', 'N/A'):.6f}°
  Longitude: {detection.get('center_lon', 'N/A'):.6f}°
  
Scores:
  Anomaly Score: {detection.get('anomaly_score', 'N/A'):.3f}
  Wreck Probability: {detection.get('wreck_probability', 'N/A'):.3f}
  
Bathymetric Analysis:
  Elevation Std: {detection.get('elevation_std', 'N/A'):.2f}m
  Elevation Range: {detection.get('elevation_range', 'N/A'):.2f}m
  Max Uncertainty: {detection.get('max_uncertainty', 'N/A'):.1f}m
  NaN Ratio: {detection.get('nan_ratio', 'N/A'):.1%}
  
Feature Detection:
  Features Count: {detection.get('features_count', 'N/A')}
  Texture Entropy: {detection.get('texture_entropy', 'N/A'):.2f}
  
Pattern Analysis:
  Smoothing Score: {detection.get('smoothing_confidence', 'N/A'):.2f}
  Freighter Likelihood: {detection.get('freighter_likelihood', 'N/A'):.2f}
  
Spatial Context:
  Nearest Wreck: {detection.get('nearest_wreck', 'N/A')}
  Distance: {detection.get('distance_to_nearest_wreck', 'N/A'):.0f}m
  
Source File: {detection.get('source_file', 'N/A')}
Tile ID: {detection.get('tile_id', 'N/A')}
"""
        
        self.info_text.insert(1.0, info_text)
    
    def update_visualization(self, detection):
        """Update the bathymetric visualization"""
        try:
            # Get source file
            source_file = detection.get('source_file', '')
            if not source_file:
                self.status_var.set("No source file information")
                return
            
            # Find the BAG file
            bag_path = self.find_bag_file(source_file)
            if not bag_path:
                self.status_var.set(f"Could not find BAG file: {source_file}")
                return
            
            # Get tile coordinates
            center_utm_x = detection.get('center_utm_x')
            center_utm_y = detection.get('center_utm_y')
            
            if center_utm_x is None or center_utm_y is None:
                self.status_var.set("No UTM coordinates available")
                return
            
            # Extract bathymetric data around the detection
            self.extract_and_plot_bathymetry(bag_path, center_utm_x, center_utm_y, detection)
            
        except Exception as e:
            self.status_var.set(f"Visualization error: {str(e)}")
    
    def find_bag_file(self, source_file):
        """Find the full path to a BAG file"""
        # Check main directory
        main_path = Path(r"c:\Temp\bagfilework") / source_file
        if main_path.exists():
            return str(main_path)
        
        # Check bathymetric_project directory
        project_path = Path(r"c:\Temp\bagfilework\bathymetric_project") / source_file
        if project_path.exists():
            return str(project_path)
        
        return None
    
    def extract_and_plot_bathymetry(self, bag_path, center_x, center_y, detection):
        """Extract and plot bathymetric data around detection point"""
        try:
            with rasterio.open(bag_path) as src:
                # Convert center coordinates to pixel coordinates
                row, col = src.index(center_x, center_y)
                
                # Define window around the point (100x100 pixels)
                window_size = 50
                window = Window(
                    col - window_size, row - window_size,
                    window_size * 2, window_size * 2
                )
                
                # Read elevation and uncertainty data
                elevation = src.read(1, window=window)
                uncertainty = src.read(2, window=window) if src.count > 1 else None
                
                # Update plots on main thread
                self.root.after(0, self.plot_bathymetry, elevation, uncertainty, detection)
                
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Plot error: {str(e)}"))
    
    def plot_bathymetry(self, elevation, uncertainty, detection):
        """Plot bathymetric data"""
        self.ax1.clear()
        self.ax2.clear()
        
        # Plot elevation
        if elevation is not None:
            im1 = self.ax1.imshow(elevation, cmap='viridis', aspect='equal')
            self.ax1.set_title('Elevation (m)')
            self.ax1.set_xlabel('Pixels')
            self.ax1.set_ylabel('Pixels')
            
            # Add center crosshairs
            center = elevation.shape[0] // 2
            self.ax1.axhline(y=center, color='red', linestyle='--', alpha=0.7)
            self.ax1.axvline(x=center, color='red', linestyle='--', alpha=0.7)
            
            plt.colorbar(im1, ax=self.ax1, shrink=0.8)
        
        # Plot uncertainty or gradient if available
        if uncertainty is not None:
            im2 = self.ax2.imshow(uncertainty, cmap='plasma', aspect='equal')
            self.ax2.set_title('Uncertainty (m)')
            plt.colorbar(im2, ax=self.ax2, shrink=0.8)
        else:
            # Calculate and plot gradient magnitude
            grad_y, grad_x = np.gradient(elevation)
            grad_mag = np.sqrt(grad_x**2 + grad_y**2)
            im2 = self.ax2.imshow(grad_mag, cmap='hot', aspect='equal')
            self.ax2.set_title('Gradient Magnitude')
            plt.colorbar(im2, ax=self.ax2, shrink=0.8)
        
        self.ax2.set_xlabel('Pixels')
        self.ax2.set_ylabel('Pixels')
        
        # Add center crosshairs to second plot
        center = elevation.shape[0] // 2
        self.ax2.axhline(y=center, color='red', linestyle='--', alpha=0.7)
        self.ax2.axvline(x=center, color='red', linestyle='--', alpha=0.7)
        
        self.fig.tight_layout()
        self.canvas.draw()
        
        self.status_var.set("Visualization updated")
    
    def load_annotation(self, detection):
        """Load existing annotation for this detection"""
        detection_id = f"{detection.get('source_file', '')}_{detection.get('tile_id', '')}"
        
        if detection_id in self.annotations:
            annotation = self.annotations[detection_id]
            self.classification_var.set(annotation.get('classification', 'Unknown'))
            self.confidence_var.set(annotation.get('confidence', 3))
            
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(1.0, annotation.get('notes', ''))
    
    def save_annotation(self, *args):
        """Save current annotation"""
        if self.filtered_df is None or len(self.filtered_df) == 0:
            return
            
        detection = self.filtered_df.iloc[self.current_index]
        detection_id = f"{detection.get('source_file', '')}_{detection.get('tile_id', '')}"
        
        self.annotations[detection_id] = {
            'classification': self.classification_var.get(),
            'confidence': self.confidence_var.get(),
            'notes': self.notes_text.get(1.0, tk.END).strip(),
            'lat': detection.get('center_lat'),
            'lon': detection.get('center_lon'),
            'anomaly_score': detection.get('anomaly_score'),
            'wreck_probability': detection.get('wreck_probability')
        }
        
        # Save to file
        self.save_annotations_to_file()
    
    def save_annotations_to_file(self):
        """Save all annotations to a file"""
        try:
            output_dir = Path(r"c:\Temp\bagfilework\enhanced_scan_results")
            output_dir.mkdir(exist_ok=True)
            
            annotations_file = output_dir / "annotations.csv"
            
            # Convert annotations to DataFrame
            if self.annotations:
                df = pd.DataFrame.from_dict(self.annotations, orient='index')
                df.index.name = 'detection_id'
                df.to_csv(annotations_file)
                
        except Exception as e:
            print(f"Error saving annotations: {e}")


def main():
    """Launch the GUI"""
    root = tk.Tk()
    app = WreckDetectionReviewGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()