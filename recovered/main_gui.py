import tkinter as tk
from tkinter import ttk
from pdf_breaker_gui import create_pdf_breaker_tab
from swayze_gui import create_swayze_tab
from bag_analyzer_gui import create_bag_analyzer_tab
from workflow_gui import create_workflow_tab
from historical_tab import create_historical_tab


def main():
    root = tk.Tk()
    root.title("Wreck Detection System")
    root.geometry("1100x700")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    notebook.add(create_pdf_breaker_tab(notebook), text="PDF Breakers")
    notebook.add(create_swayze_tab(notebook), text="Swayze Database")
    notebook.add(create_bag_analyzer_tab(notebook), text="BAG File Analyzer")
    notebook.add(create_workflow_tab(notebook), text="Workflow")
    notebook.add(create_historical_tab(notebook), text="Historical Drift")

    root.mainloop()


if __name__ == "__main__":
    main()
