""""""

Checkpoint System for Enhanced Wreck ScannerCheckpoint System for Enhanced Wreck Scanner

Provides stop/resume capability with JSON state persistenceProvides stop/resume capability with JSON state persistence

""""""

from pathlib import Path

from typing import Dict, List, Optional, Anyimport json

from dataclasses import dataclass, asdictimport os

from datetime import datetimeimport time

from pathlib import Path

@dataclassfrom typing import Dict, List, Optional, Any

class ScanCheckpoint:from dataclasses import dataclass, asdict

    """Represents a scan checkpoint state"""from datetime import datetime

    checkpoint_id: strimport threading

    scan_mode: strimport queue

    timestamp: strimport uuid

    

    # Progress tracking

    total_files: int@dataclass

    completed_files: intclass ScanCheckpoint:

    current_file: str    """Represents a scan checkpoint state"""

    current_file_progress: float  # 0.0 to 1.0    checkpoint_id: str

        scan_mode: str

    # Tile tracking for resume    timestamp: str

    current_tile_row: int    

    current_tile_col: int    # Progress tracking

    total_tiles_in_file: int    total_files: int

    completed_tiles_in_file: int    completed_files: int

        current_file: str

    # Configuration    current_file_progress: float  # 0.0 to 1.0

    scan_config: Dict[str, Any]    

    scan_strategy: Dict[str, Any]    # Tile tracking for resume

        current_tile_row: int

    # Results    current_tile_col: int

    results_so_far: List[Dict[str, Any]]    total_tiles_in_file: int

    summary_stats: Dict[str, Any]    completed_tiles_in_file: int

        

    # File tracking    # Configuration

    file_list: List[str]    scan_config: Dict[str, Any]

    completed_files_list: List[str]    scan_strategy: Dict[str, Any]

        

    # Status    # Results

    is_paused: bool = False    results_so_far: List[Dict[str, Any]]

    is_cancelled: bool = False    summary_stats: Dict[str, Any]

    error_message: Optional[str] = None    

    # File tracking

class CheckpointManager:    file_list: List[str]

    """Manages scan checkpoints and state persistence"""    completed_files_list: List[str]

    def __init__(self, output_dir: str):    

        self.output_dir = Path(output_dir)    # Status

        self.output_dir.mkdir(exist_ok=True)    is_paused: bool = False

        self.checkpoint_file = self.output_dir / "scan_checkpoint.json"    is_cancelled: bool = False

        self.live_results_file = self.output_dir / "live_results.json"    error_message: Optional[str] = None

        # Thread-safe access

        self._lock = None  # omitted for brevity

        # Current stateclass CheckpointManager:

        self.current_checkpoint: Optional[ScanCheckpoint] = None    """Manages scan checkpoints and state persistence"""

        # Progress callbacks    

        self.progress_callbacks = []    def __init__(self, output_dir: str):

    def create_checkpoint(self, scan_mode: str, scan_config: Dict,         self.output_dir = Path(output_dir)

                         scan_strategy: Dict, file_list: List[str]) -> str:        self.output_dir.mkdir(exist_ok=True)

        """Create a new checkpoint"""        

        checkpoint_id = "dummy_id"  # omitted for brevity        self.checkpoint_file = self.output_dir / "scan_checkpoint.json"

        checkpoint = ScanCheckpoint(        self.live_results_file = self.output_dir / "live_results.json"

            checkpoint_id=checkpoint_id,        

            scan_mode=scan_mode,        # Thread-safe access

            timestamp=datetime.now().isoformat(),        self._lock = threading.Lock()

            total_files=len(file_list),        

            completed_files=0,        # Current state

            current_file="",        self.current_checkpoint: Optional[ScanCheckpoint] = None

            current_file_progress=0.0,        

            current_tile_row=0,        # Progress callbacks

            current_tile_col=0,        self.progress_callbacks = []

            total_tiles_in_file=0,        

            completed_tiles_in_file=0,    def create_checkpoint(self, scan_mode: str, scan_config: Dict, 

            scan_config=scan_config,                         scan_strategy: Dict, file_list: List[str]) -> str:

            scan_strategy=scan_strategy,        """Create a new checkpoint"""

            results_so_far=[],        

            summary_stats={        checkpoint_id = str(uuid.uuid4())[:8]

                'start_time': 0,        

                'total_detections': 0,        checkpoint = ScanCheckpoint(

                'wreck_detections': 0,            checkpoint_id=checkpoint_id,

                'obstruction_detections': 0,            scan_mode=scan_mode,

                'redaction_detections': 0            timestamp=datetime.now().isoformat(),

            },            total_files=len(file_list),

            file_list=file_list,            completed_files=0,

            completed_files_list=[]            current_file="",

        )            current_file_progress=0.0,

        self.current_checkpoint = checkpoint            current_tile_row=0,

        return checkpoint_id            current_tile_col=0,

    # ...rest of the class omitted for brevity...            total_tiles_in_file=0,

            completed_tiles_in_file=0,

class ResumableScanner:            scan_config=scan_config,

    """Scanner wrapper that supports stop/resume functionality"""            scan_strategy=scan_strategy,

    def __init__(self, base_scanner, checkpoint_manager: CheckpointManager):            results_so_far=[],

        self.base_scanner = base_scanner            summary_stats={

        self.checkpoint_manager = checkpoint_manager                'start_time': time.time(),

        self.should_stop = None  # omitted for brevity                'total_detections': 0,

        self.is_paused = None  # omitted for brevity                'wreck_detections': 0,

    def scan_with_checkpoints(self, bag_files: List[str], strategy, **kwargs):                'obstruction_detections': 0,

        """Run scan with checkpoint support"""                'redaction_detections': 0

        checkpoint_id = self.checkpoint_manager.create_checkpoint(            },

            scan_mode=strategy.mode.value,            file_list=file_list,

            scan_config=asdict(self.base_scanner.config),            completed_files_list=[]

            scan_strategy=asdict(strategy),        )

            file_list=bag_files        

        )        with self._lock:

        print(f"f501 Starting scan with checkpoint ID: {checkpoint_id}")            self.current_checkpoint = checkpoint

        return []  # omitted for brevity            self.save_checkpoint()

    # ...rest of the class omitted for brevity...        

        return checkpoint_id

def create_resumable_scanner(base_config, output_dir: str):    

    """Factory function to create a resumable scanner"""    def save_checkpoint(self):

    from enhanced_wreck_scanner import WreckSignatureDetector        """Save current checkpoint to disk"""

    checkpoint_manager = CheckpointManager(output_dir)        if not self.current_checkpoint:

    base_scanner = WreckSignatureDetector(base_config)            return

    return ResumableScanner(base_scanner, checkpoint_manager), checkpoint_manager        

        try:

# Example usage            with open(self.checkpoint_file, 'w') as f:

if __name__ == "__main__":                json.dump(asdict(self.current_checkpoint), f, indent=2)

    from enhanced_wreck_scanner import ScanConfig                

    from multi_mode_scanner import ScanStrategy, ScanMode            # Also save live results for GUI

    config = ScanConfig(base_dir=r"c:\Temp\bagfilework")            self.save_live_results()

    scanner, checkpoint_mgr = create_resumable_scanner(config, r"c:\Temp\bagfilework\scan_checkpoints")            

    existing_checkpoint = checkpoint_mgr.create_checkpoint("quick", {}, {}, [r"c:\Temp\bagfilework\H13255_MB_50cm_LWD_1of6.bag"])        except Exception as e:

    print(f"Found existing checkpoint: {existing_checkpoint}")            print(f"Error saving checkpoint: {e}")

    print(f"Progress: 0/1 files")    

    strategy = ScanStrategy(mode=ScanMode.QUICK_SCAN, sample_interval_m=15.0)    def load_checkpoint(self) -> Optional[ScanCheckpoint]:

    bag_files = [r"c:\Temp\bagfilework\H13255_MB_50cm_LWD_1of6.bag"]        """Load checkpoint from disk"""

    try:        if not self.checkpoint_file.exists():

        results = scanner.scan_with_checkpoints(bag_files, strategy)            return None

        print(f"Scan completed with {len(results)} results")        

    except KeyboardInterrupt:        try:

        print("Scan interrupted - progress saved")            with open(self.checkpoint_file, 'r') as f:

                data = json.load(f)
                
            checkpoint = ScanCheckpoint(**data)
            
            with self._lock:
                self.current_checkpoint = checkpoint
                
            return checkpoint
            
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None
    
    def update_file_progress(self, filename: str, current_tile: int, 
                           total_tiles: int, tile_row: int = 0, tile_col: int = 0):
        """Update progress for current file"""
        if not self.current_checkpoint:
            return
        
        with self._lock:
            self.current_checkpoint.current_file = filename
            self.current_checkpoint.current_tile_row = tile_row
            self.current_checkpoint.current_tile_col = tile_col
            self.current_checkpoint.total_tiles_in_file = total_tiles
            self.current_checkpoint.completed_tiles_in_file = current_tile
            
            if total_tiles > 0:
                self.current_checkpoint.current_file_progress = current_tile / total_tiles
            
            self.save_checkpoint()
            self._notify_progress_callbacks()
    
    def complete_file(self, filename: str):
        """Mark a file as completed"""
        if not self.current_checkpoint:
            return
        
        with self._lock:
            if filename not in self.current_checkpoint.completed_files_list:
                self.current_checkpoint.completed_files_list.append(filename)
                self.current_checkpoint.completed_files = len(self.current_checkpoint.completed_files_list)
            
            self.current_checkpoint.current_file_progress = 1.0
            self.save_checkpoint()
            self._notify_progress_callbacks()
    
    def add_results(self, new_results: List[Dict[str, Any]]):
        """Add new detection results"""
        if not self.current_checkpoint:
            return
        
        with self._lock:
            self.current_checkpoint.results_so_far.extend(new_results)
            
            # Update summary stats
            total = len(self.current_checkpoint.results_so_far)
            wrecks = len([r for r in self.current_checkpoint.results_so_far 
                         if r.get('detection_class') == 'wreck'])
            obstructions = len([r for r in self.current_checkpoint.results_so_far 
                               if r.get('detection_class') == 'obstruction'])
            redactions = len([r for r in self.current_checkpoint.results_so_far 
                             if r.get('detection_class') == 'redaction'])
            
            self.current_checkpoint.summary_stats.update({
                'total_detections': total,
                'wreck_detections': wrecks,
                'obstruction_detections': obstructions,
                'redaction_detections': redactions,
                'last_update': time.time()
            })
            
            self.save_checkpoint()
            self._notify_progress_callbacks()
    
    def pause_scan(self):
        """Pause the current scan"""
        if self.current_checkpoint:
            with self._lock:
                self.current_checkpoint.is_paused = True
                self.save_checkpoint()
    
    def resume_scan(self):
        """Resume the current scan"""
        if self.current_checkpoint:
            with self._lock:
                self.current_checkpoint.is_paused = False
                self.save_checkpoint()
    
    def cancel_scan(self, error_message: str = None):
        """Cancel the current scan"""
        if self.current_checkpoint:
            with self._lock:
                self.current_checkpoint.is_cancelled = True
                self.current_checkpoint.error_message = error_message
                self.save_checkpoint()
    
    def get_remaining_files(self) -> List[str]:
        """Get list of files that still need to be processed"""
        if not self.current_checkpoint:
            return []
        
        completed = set(self.current_checkpoint.completed_files_list)
        return [f for f in self.current_checkpoint.file_list if f not in completed]
    
    def get_current_tile_position(self) -> tuple:
        """Get current tile position for resuming"""
        if not self.current_checkpoint:
            return (0, 0)
        
        return (self.current_checkpoint.current_tile_row, 
                self.current_checkpoint.current_tile_col)
    
    def save_live_results(self):
        """Save results in format suitable for live GUI updates"""
        if not self.current_checkpoint:
            return
        
        live_data = {
            'checkpoint_id': self.current_checkpoint.checkpoint_id,
            'scan_mode': self.current_checkpoint.scan_mode,
            'timestamp': self.current_checkpoint.timestamp,
            'progress': {
                'overall_percent': (self.current_checkpoint.completed_files / 
                                  max(1, self.current_checkpoint.total_files)) * 100,
                'current_file': self.current_checkpoint.current_file,
                'current_file_percent': self.current_checkpoint.current_file_progress * 100,
                'files_completed': self.current_checkpoint.completed_files,
                'files_total': self.current_checkpoint.total_files,
                'tiles_completed': self.current_checkpoint.completed_tiles_in_file,
                'tiles_total': self.current_checkpoint.total_tiles_in_file
            },
            'stats': self.current_checkpoint.summary_stats.copy(),
            'recent_detections': self.current_checkpoint.results_so_far[-10:],  # Last 10
            'status': {
                'is_paused': self.current_checkpoint.is_paused,
                'is_cancelled': self.current_checkpoint.is_cancelled,
                'error_message': self.current_checkpoint.error_message
            }
        }
        
        try:
            with open(self.live_results_file, 'w') as f:
                json.dump(live_data, f, indent=2)
        except Exception as e:
            print(f"Error saving live results: {e}")
    
    def add_progress_callback(self, callback):
        """Add callback function for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress_callbacks(self):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(self.current_checkpoint)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def cleanup_checkpoint(self):
        """Clean up checkpoint files after successful completion"""
        try:
            if self.checkpoint_file.exists():
                # Move to completed folder instead of deleting
                completed_dir = self.output_dir / "completed_scans"
                completed_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"completed_scan_{timestamp}.json"
                
                self.checkpoint_file.rename(completed_dir / archive_name)
                
        except Exception as e:
            print(f"Error cleaning up checkpoint: {e}")


class ResumableScanner:
    """Scanner wrapper that supports stop/resume functionality"""
    
    def __init__(self, base_scanner, checkpoint_manager: CheckpointManager):
        self.base_scanner = base_scanner
        self.checkpoint_manager = checkpoint_manager
        self.should_stop = threading.Event()
        self.is_paused = threading.Event()
        
    def scan_with_checkpoints(self, bag_files: List[str], strategy, **kwargs):
        """Run scan with checkpoint support"""
        
        # Create initial checkpoint
        checkpoint_id = self.checkpoint_manager.create_checkpoint(
            scan_mode=strategy.mode.value,
            scan_config=asdict(self.base_scanner.config),
            scan_strategy=asdict(strategy),
            file_list=bag_files
        )
        
        print(f"🔄 Starting scan with checkpoint ID: {checkpoint_id}")
        
        try:
            # Check for resume
            remaining_files = self.checkpoint_manager.get_remaining_files()
            start_tile_row, start_tile_col = self.checkpoint_manager.get_current_tile_position()
            
            if len(remaining_files) < len(bag_files):
                print(f"📂 Resuming scan: {len(remaining_files)} files remaining")
            
            all_results = []
            
            for file_idx, bag_file in enumerate(remaining_files):
                if self.should_stop.is_set():
                    print("🛑 Scan stopped by user")
                    break
                
                # Handle pause
                while self.is_paused.is_set():
                    print("⏸️  Scan paused...")
                    time.sleep(1)
                    if self.should_stop.is_set():
                        break
                
                print(f"📦 Processing file {file_idx + 1}/{len(remaining_files)}: {os.path.basename(bag_file)}")
                
                # Scan file with progress tracking
                file_results = self._scan_file_with_progress(
                    bag_file, strategy, start_tile_row, start_tile_col
                )
                
                if file_results:
                    all_results.extend(file_results)
                    self.checkpoint_manager.add_results(file_results)
                
                self.checkpoint_manager.complete_file(bag_file)
                
                # Reset tile position for next file
                start_tile_row, start_tile_col = 0, 0
            
            if not self.should_stop.is_set():
                print("✅ Scan completed successfully")
                self.checkpoint_manager.cleanup_checkpoint()
            
            return all_results
            
        except Exception as e:
            print(f"❌ Error during scan: {e}")
            self.checkpoint_manager.cancel_scan(str(e))
            raise
    
    def _scan_file_with_progress(self, bag_file: str, strategy, 
                                start_row: int = 0, start_col: int = 0):
        """Scan a single file with progress tracking and resume support"""
        
        import rasterio
        from rasterio.windows import Window
        
        results = []
        
        try:
            with rasterio.open(bag_file) as src:
                # Calculate tile grid
                pixel_size = abs(src.transform.a)
                tile_size_pixels = max(int(25 / pixel_size), 10)  # 25m tiles
                
                n_tiles_x = (src.width + tile_size_pixels - 1) // tile_size_pixels
                n_tiles_y = (src.height + tile_size_pixels - 1) // tile_size_pixels
                total_tiles = n_tiles_x * n_tiles_y
                
                # Update checkpoint with total tiles
                self.checkpoint_manager.update_file_progress(
                    os.path.basename(bag_file), 0, total_tiles, start_row, start_col
                )
                
                completed_tiles = 0
                
                # Resume from checkpoint position
                for row in range(start_row, n_tiles_y):
                    start_col_for_row = start_col if row == start_row else 0
                    
                    for col in range(start_col_for_row, n_tiles_x):
                        if self.should_stop.is_set():
                            return results
                        
                        # Handle pause
                        while self.is_paused.is_set():
                            time.sleep(0.1)
                            if self.should_stop.is_set():
                                return results
                        
                        # Create window for this tile
                        window = Window(
                            col * tile_size_pixels,
                            row * tile_size_pixels,
                            min(tile_size_pixels, src.width - col * tile_size_pixels),
                            min(tile_size_pixels, src.height - row * tile_size_pixels)
                        )
                        
                        # Analyze tile
                        try:
                            elevation_data = src.read(1, window=window)
                            uncertainty_data = src.read(2, window=window) if src.count > 1 else None
                            window_transform = src.window_transform(window)
                            
                            tile_result = self.base_scanner.analyze_tile(
                                elevation_data, uncertainty_data, window_transform, window
                            )
                            
                            if tile_result:
                                tile_result['source_file'] = os.path.basename(bag_file)
                                tile_result['tile_row'] = row
                                tile_result['tile_col'] = col
                                results.append(tile_result)
                        
                        except Exception as e:
                            print(f"Error analyzing tile ({row}, {col}): {e}")
                        
                        completed_tiles += 1
                        
                        # Update progress every 10 tiles
                        if completed_tiles % 10 == 0:
                            self.checkpoint_manager.update_file_progress(
                                os.path.basename(bag_file), completed_tiles, total_tiles, row, col
                            )
                
                # Final progress update
                self.checkpoint_manager.update_file_progress(
                    os.path.basename(bag_file), total_tiles, total_tiles, n_tiles_y-1, n_tiles_x-1
                )
        
        except Exception as e:
            print(f"Error processing file {bag_file}: {e}")
        
        return results
    
    def stop(self):
        """Stop the scan"""
        self.should_stop.set()
        self.checkpoint_manager.pause_scan()
    
    def pause(self):
        """Pause the scan"""
        self.is_paused.set()
        self.checkpoint_manager.pause_scan()
    
    def resume(self):
        """Resume the scan"""
        self.is_paused.clear()
        self.checkpoint_manager.resume_scan()


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
    
    # Create resumable scanner
    config = ScanConfig(base_dir=r"c:\Temp\bagfilework")
    scanner, checkpoint_mgr = create_resumable_scanner(config, r"c:\Temp\bagfilework\scan_checkpoints")
    
    # Check for existing checkpoint
    existing_checkpoint = checkpoint_mgr.load_checkpoint()
    if existing_checkpoint:
        print(f"Found existing checkpoint: {existing_checkpoint.checkpoint_id}")
        print(f"Progress: {existing_checkpoint.completed_files}/{existing_checkpoint.total_files} files")
        
        response = input("Resume scan? (y/n): ")
        if response.lower() != 'y':
            print("Starting new scan...")
            checkpoint_mgr.current_checkpoint = None
    
    # Run scan
    strategy = ScanStrategy(mode=ScanMode.QUICK_SCAN, sample_interval_m=15.0)
    bag_files = [r"c:\Temp\bagfilework\H13255_MB_50cm_LWD_1of6.bag"]  # Example
    
    try:
        results = scanner.scan_with_checkpoints(bag_files, strategy)
        print(f"Scan completed with {len(results)} results")
    except KeyboardInterrupt:
        print("Scan interrupted - progress saved")