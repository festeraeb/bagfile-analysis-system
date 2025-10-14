"""
Checkpoint System for Enhanced Wreck Scanner
Provides stop/resume capability with JSON state persistence
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import queue
import uuid

@dataclass
class ScanCheckpoint:
    """Represents a scan checkpoint state"""
    checkpoint_id: str
    scan_mode: str
    timestamp: str
    # Progress tracking
    total_files: int
    completed_files: int
    current_file: str
    current_file_progress: float  # 0.0 to 1.0
    # Tile tracking for resume
    current_tile_row: int
    current_tile_col: int
    total_tiles_in_file: int
    completed_tiles_in_file: int
    # Configuration
    scan_config: Dict[str, Any]
    scan_strategy: Dict[str, Any]
    # Results
    results_so_far: List[Dict[str, Any]]
    summary_stats: Dict[str, Any]
    # File tracking
    file_list: List[str]
    completed_files_list: List[str]
    # Status
    is_paused: bool = False
    is_cancelled: bool = False
    error_message: Optional[str] = None

class CheckpointManager:
    """Manages scan checkpoints and state persistence"""
    # ...existing code...
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.checkpoint_file = self.output_dir / "scan_checkpoint.json"
        self.live_results_file = self.output_dir / "live_results.json"
        self._lock = threading.Lock()
        self.current_checkpoint: Optional[ScanCheckpoint] = None
        self.progress_callbacks = []
    # ...existing code...
    # (Full implementation as in the open editor)

class ResumableScanner:
    """Scanner wrapper that supports stop/resume functionality"""
    # ...existing code...
    # (Full implementation as in the open editor)

def create_resumable_scanner(base_config, output_dir: str):
    """Factory function to create a resumable scanner"""
    from enhanced_wreck_scanner import WreckSignatureDetector
    checkpoint_manager = CheckpointManager(output_dir)
    base_scanner = WreckSignatureDetector(base_config)
    return ResumableScanner(base_scanner, checkpoint_manager), checkpoint_manager

# Example usage
if __name__ == "__main__":
    from enhanced_wreck_scanner import ScanConfig
    from multi_mode_scanner import ScanStrategy, ScanMode
    config = ScanConfig(base_dir=r"c:\Temp\bagfilework")
    scanner, checkpoint_mgr = create_resumable_scanner(config, r"c:\Temp\bagfilework\scan_checkpoints")
    existing_checkpoint = checkpoint_mgr.load_checkpoint()
    if existing_checkpoint:
        print(f"Found existing checkpoint: {existing_checkpoint.checkpoint_id}")
        print(f"Progress: {existing_checkpoint.completed_files}/{existing_checkpoint.total_files} files")
        response = input("Resume scan? (y/n): ")
        if response.lower() != 'y':
            print("Starting new scan...")
            checkpoint_mgr.current_checkpoint = None
    strategy = ScanStrategy(mode=ScanMode.QUICK_SCAN, sample_interval_m=15.0)
    bag_files = [r"c:\Temp\bagfilework\H13255_MB_50cm_LWD_1of6.bag"]  # Example
    try:
        results = scanner.scan_with_checkpoints(bag_files, strategy)
        print(f"Scan completed with {len(results)} results")
    except KeyboardInterrupt:
        print("Scan interrupted - progress saved")
