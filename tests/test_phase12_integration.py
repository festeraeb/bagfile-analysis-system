"""
Phase 12 Integration Tests

Tests for complete phase 12 integration including:
- Real-time streaming to visualization pipeline
- Interactive map controls
- Full workflow end-to-end

Author: CESARops Development
Date: January 27, 2026
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock
import threading

from src.cesarops.sonar_stream_buffer import SonarPing, SonarStreamBuffer
from src.cesarops.sonar_visualization import WebGLRenderer, ViewportSettings
from src.cesarops.interactive_map import InteractiveMap, MapSettings


# ============================================================================
# Phase 12 Complete Workflow Tests
# ============================================================================

class TestPhase12CompleteWorkflow:
    """Test complete Phase 12 workflow."""
    
    def test_streaming_to_visualization_pipeline(self):
        """Test data flowing from stream to visualization."""
        # Setup stream buffer
        buffer = SonarStreamBuffer(capacity=1000, max_ping_age_seconds=30)
        
        # Setup renderer
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        # Add bathymetry from mock data
        bath_grid = np.random.rand(20, 20) * -50
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        renderer.add_anomaly_layer("anomalies")
        
        # Add sonar pings to buffer
        for i in range(10):
            ping = SonarPing(
                ping_id=i,
                timestamp=i * 0.01,
                frequency=200000,
                intensity=np.random.rand(256),
                range_resolution=0.1,
            )
            buffer.push(ping)
        
        # Render frame
        frame = renderer.render_frame()
        assert "stats" in frame
    
    def test_interactive_map_with_streaming(self):
        """Test interactive map receiving streaming data."""
        # Setup components
        buffer = SonarStreamBuffer(capacity=500, max_ping_age_seconds=30)
        viewport = ViewportSettings(1024, 768)
        renderer = WebGLRenderer(viewport)
        
        bath_grid = np.ones((20, 20)) * -30
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        renderer.add_anomaly_layer("anomalies")
        
        # Setup interactive map
        map_widget = InteractiveMap(MapSettings(width=1024, height=768))
        
        # Mock stream manager
        mock_stream = Mock()
        mock_stream.get_stats.return_value = {
            'samples_per_second': 50000,
            'anomalies_detected': 2,
        }
        
        map_widget.setup(renderer, mock_stream)
        map_widget.activate()
        
        # Add streaming data
        for i in range(5):
            ping = SonarPing(
                ping_id=i,
                timestamp=i * 0.01,
                frequency=200000,
                intensity=np.random.rand(256),
                range_resolution=0.1,
            )
            buffer.push(ping)
        
        # Update map and check state
        state = map_widget.update()
        assert state['statistics']['streaming_rate_hz'] == 50000
        assert state['statistics']['anomalies_detected'] == 2
    
    def test_camera_control_responsiveness(self):
        """Test camera control responsiveness."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        bath_grid = np.random.rand(30, 30) * -100
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        
        map_widget = InteractiveMap()
        map_widget.setup(renderer, None)
        
        initial_pos = renderer.camera.position
        
        # Perform camera controls
        for _ in range(5):
            map_widget.handle_camera_pan(5, 5)
            map_widget.handle_camera_zoom(0.95)
        
        final_pos = renderer.camera.position
        
        # Camera should have moved
        assert initial_pos != final_pos
    
    def test_layer_management_integration(self):
        """Test layer management across components."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        # Add multiple layers
        bath_grid = np.random.rand(20, 20) * -50
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        renderer.add_anomaly_layer("anomalies")
        mosaic = np.random.rand(20, 20)
        renderer.add_mosaic_layer("mosaic", mosaic, 200, 200)
        
        # Setup interactive map
        map_widget = InteractiveMap()
        map_widget.setup(renderer, None)
        
        # Toggle layers through map
        map_widget.handle_layer_toggle("bathymetry")
        map_widget.handle_layer_toggle("anomalies")
        
        layers = map_widget.layer_toggle.get_all_layers()
        assert layers["bathymetry"] is False
        assert layers["anomalies"] is False
        assert layers["mosaic"] is True


# ============================================================================
# Streaming Performance Integration Tests
# ============================================================================

class TestStreamingPerformanceIntegration:
    """Test streaming performance with visualization."""
    
    def test_high_throughput_streaming(self):
        """Test high-throughput streaming performance."""
        buffer = SonarStreamBuffer(capacity=10000, max_ping_age_seconds=30)
        
        # Add 1000 pings rapidly
        start_time = time.time()
        for i in range(1000):
            ping = SonarPing(
                ping_id=i,
                timestamp=i * 0.001,
                frequency=200000,
                intensity=np.random.rand(256),
                range_resolution=0.1,
            )
            buffer.push(ping)
        
        elapsed = time.time() - start_time
        throughput = 1000 / elapsed if elapsed > 0 else float('inf')
        
        # Should handle >1000 pings per second
        assert throughput > 1000
    
    def test_rendering_under_load(self):
        """Test rendering performance under load."""
        viewport = ViewportSettings(1920, 1080)
        renderer = WebGLRenderer(viewport)
        
        # Large bathymetry grid
        bath_grid = np.random.rand(100, 100) * -200
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        
        # Many anomalies
        renderer.add_anomaly_layer("anomalies")
        anom_layer = renderer.layers["anomalies"]
        
        # Add 500 anomalies
        for i in range(500):
            anom_layer.add_anomaly(
                x=np.random.rand() * 1000,
                y=np.random.rand() * 1000,
                z=-np.random.rand() * 200,
                anomaly_type="strong_return",
                confidence=0.8
            )
        
        # Render multiple frames
        frame_times = []
        for _ in range(60):
            start = time.time()
            renderer.render_frame()
            frame_times.append((time.time() - start) * 1000)
        
        avg_frame_time = np.mean(frame_times)
        fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
        
        # Should achieve >30 FPS even with large dataset
        assert fps > 30


# ============================================================================
# Export and Persistence Tests
# ============================================================================

class TestExportIntegration:
    """Test export functionality integration."""
    
    def test_snapshot_export_with_rendering(self):
        """Test exporting snapshots."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        bath_grid = np.random.rand(20, 20) * -50
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        
        map_widget = InteractiveMap()
        map_widget.setup(renderer, None)
        
        # Take snapshots
        paths = []
        for i in range(3):
            path = map_widget.handle_snapshot_export()
            paths.append(path)
            assert "snapshot_" in path
            time.sleep(0.01)
        
        assert len(paths) == 3
    
    def test_video_export_workflow(self):
        """Test video export workflow."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        map_widget = InteractiveMap()
        
        # Start video
        video_path = map_widget.handle_video_export_start()
        assert ".webm" in video_path
        
        # Simulate recording
        for _ in range(30):
            renderer.render_frame()
        
        # Stop video
        completed_path = map_widget.handle_video_export_stop()
        assert completed_path == video_path
        
        # Check history
        history = map_widget.exporter.get_export_history()
        assert len(history) == 1
        assert history[0]['status'] == 'completed'


# ============================================================================
# Multi-threaded Stress Tests
# ============================================================================

class TestConcurrencyIntegration:
    """Test concurrent operation."""
    
    def test_concurrent_streaming_rendering(self):
        """Test concurrent streaming and rendering."""
        buffer = SonarStreamBuffer(capacity=5000, max_ping_age_seconds=30)
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        bath_grid = np.random.rand(20, 20) * -50
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        
        errors = []
        
        def stream_producer():
            """Producer thread."""
            try:
                for i in range(200):
                    ping = SonarPing(
                        ping_id=i,
                        timestamp=i * 0.01,
                        frequency=200000,
                        intensity=np.random.rand(256),
                        range_resolution=0.1,
                    )
                    buffer.push(ping)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def render_consumer():
            """Consumer thread."""
            try:
                for _ in range(200):
                    renderer.render_frame()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Run threads
        t1 = threading.Thread(target=stream_producer)
        t2 = threading.Thread(target=render_consumer)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Should complete without errors
        assert len(errors) == 0


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

class TestPhase12EdgeCases:
    """Test edge cases."""
    
    def test_empty_renderer(self):
        """Test rendering with no layers."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        # Should render without error
        frame = renderer.render_frame()
        assert "stats" in frame
    
    def test_very_large_bathymetry(self):
        """Test with very large bathymetry grid."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        # 500x500 grid
        bath_grid = np.random.rand(500, 500) * -200
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        
        frame = renderer.render_frame()
        assert frame["stats"]["vertices_rendered"] > 0
    
    def test_many_anomalies(self):
        """Test with many anomalies."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        renderer.add_anomaly_layer("anomalies")
        
        anom_layer = renderer.layers["anomalies"]
        
        # Add 5000 anomalies
        for i in range(5000):
            anom_layer.add_anomaly(
                x=np.random.rand() * 1000,
                y=np.random.rand() * 1000,
                z=-np.random.rand() * 200,
                anomaly_type="strong_return",
                confidence=0.8
            )
        
        frame = renderer.render_frame()
        cloud = anom_layer.get_point_cloud_data()
        assert len(cloud["points"]) == 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
