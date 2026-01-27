"""
Unit Tests for Interactive Map Module (Phase 12.3)

Tests for layer controls, statistics, export, and navigation.

Author: CESARops Development
Date: January 27, 2026
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, MagicMock

from src.cesarops.interactive_map import (
    MapSettings, LayerToggle, StatisticsPanel, SnapshotExporter,
    NavigationControls, InteractiveMap
)


# ============================================================================
# MapSettings Tests
# ============================================================================

class TestMapSettings:
    """Test map configuration."""
    
    def test_default_settings(self):
        """Test default settings."""
        settings = MapSettings()
        assert settings.width == 1024
        assert settings.height == 768
        assert settings.enable_keyboard is True
        assert settings.export_format == "png"
    
    def test_custom_settings(self):
        """Test custom settings."""
        settings = MapSettings(width=1920, height=1080, enable_mouse=False)
        assert settings.width == 1920
        assert settings.height == 1080
        assert settings.enable_mouse is False


# ============================================================================
# LayerToggle Tests
# ============================================================================

class TestLayerToggle:
    """Test layer visibility controls."""
    
    def test_add_layer(self):
        """Test adding layer."""
        toggle = LayerToggle()
        toggle.add_layer("bathymetry", visible=True)
        toggle.add_layer("anomalies", visible=False)
        
        assert toggle.get_layer_state("bathymetry") is True
        assert toggle.get_layer_state("anomalies") is False
    
    def test_toggle_layer(self):
        """Test toggling layer visibility."""
        toggle = LayerToggle()
        toggle.add_layer("bathymetry", visible=True)
        
        result = toggle.toggle_layer("bathymetry")
        assert result is False
        
        result = toggle.toggle_layer("bathymetry")
        assert result is True
    
    def test_set_layer_visible(self):
        """Test setting layer visibility."""
        toggle = LayerToggle()
        toggle.add_layer("layer1", visible=False)
        
        toggle.set_layer_visible("layer1", True)
        assert toggle.get_layer_state("layer1") is True
    
    def test_get_visible_layers(self):
        """Test getting visible layers."""
        toggle = LayerToggle()
        toggle.add_layer("bath", visible=True)
        toggle.add_layer("anom", visible=False)
        toggle.add_layer("mosaic", visible=True)
        
        visible = toggle.get_visible_layers()
        assert "bath" in visible
        assert "anom" not in visible
        assert "mosaic" in visible
    
    def test_get_all_layers(self):
        """Test getting all layers."""
        toggle = LayerToggle()
        toggle.add_layer("bath", visible=True)
        toggle.add_layer("anom", visible=False)
        
        all_layers = toggle.get_all_layers()
        assert len(all_layers) == 2
        assert all_layers["bath"] is True
        assert all_layers["anom"] is False


# ============================================================================
# StatisticsPanel Tests
# ============================================================================

class TestStatisticsPanel:
    """Test statistics display."""
    
    def test_creation(self):
        """Test creating statistics panel."""
        panel = StatisticsPanel(update_hz=60)
        assert panel.update_hz == 60
        assert panel.fps == 0.0
    
    def test_update_from_renderer(self):
        """Test updating from renderer stats."""
        panel = StatisticsPanel()
        
        render_stats = {
            'fps': 45.5,
            'frame_time_ms': 22.0,
            'vertices_rendered': 5000,
        }
        
        panel.update_from_renderer(render_stats)
        
        assert panel.fps == 45.5
        assert panel.frame_time_ms == 22.0
        assert panel.vertices_rendered == 5000
    
    def test_update_streaming_stats(self):
        """Test updating streaming stats."""
        panel = StatisticsPanel()
        panel.update_streaming_stats(rate_hz=1000.0, anomalies=5)
        
        assert panel.streaming_rate_hz == 1000.0
        assert panel.anomalies_detected == 5
    
    def test_get_stats_dict(self):
        """Test getting stats as dict."""
        panel = StatisticsPanel()
        
        panel.fps = 60.0
        panel.frame_time_ms = 16.67
        panel.vertices_rendered = 10000
        panel.anomalies_detected = 3
        
        stats = panel.get_stats_dict()
        
        assert stats['fps'] == 60.0
        assert stats['frame_time_ms'] == 16.67
        assert stats['vertices_rendered'] == 10000
        assert stats['anomalies_detected'] == 3
    
    def test_average_fps(self):
        """Test FPS average calculation."""
        panel = StatisticsPanel(update_hz=1000)  # Fast updates
        
        # Directly set FPS values in history instead of using update interval
        fps_values = [30.0, 40.0, 50.0, 60.0]
        for fps in fps_values:
            panel._history['fps'].append(fps)
        
        avg_fps = panel.get_average_fps()
        assert 40 <= avg_fps <= 60


# ============================================================================
# SnapshotExporter Tests
# ============================================================================

class TestSnapshotExporter:
    """Test snapshot and video export."""
    
    def test_creation(self):
        """Test creating exporter."""
        exporter = SnapshotExporter(export_dir="outputs")
        assert exporter.export_dir == "outputs"
        assert exporter.snapshot_format == "png"
    
    def test_export_snapshot(self):
        """Test exporting snapshot."""
        exporter = SnapshotExporter()
        
        frame_data = np.zeros((100, 100, 3), dtype=np.uint8)
        filepath = exporter.export_snapshot(frame_data, "test_snap.png")
        
        assert "test_snap.png" in filepath
        assert "outputs" in filepath
    
    def test_snapshot_auto_filename(self):
        """Test auto-generated snapshot filename."""
        exporter = SnapshotExporter()
        
        frame_data = np.zeros((100, 100, 3), dtype=np.uint8)
        filepath = exporter.export_snapshot(frame_data)
        
        assert "snapshot_" in filepath
        assert ".png" in filepath
    
    def test_video_export_start_stop(self):
        """Test video export lifecycle."""
        exporter = SnapshotExporter()
        
        start_path = exporter.start_video_export("test_video.webm")
        assert "test_video.webm" in start_path
        
        stop_path = exporter.stop_video_export()
        assert stop_path == start_path
    
    def test_export_history(self):
        """Test export history tracking."""
        exporter = SnapshotExporter()
        
        frame_data = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Export snapshot
        exporter.export_snapshot(frame_data, "snap1.png")
        
        # Video export
        exporter.start_video_export("vid1.webm")
        exporter.stop_video_export()
        
        history = exporter.get_export_history()
        assert len(history) == 2
        assert history[0]['type'] == 'snapshot'
        assert history[1]['type'] == 'video'


# ============================================================================
# NavigationControls Tests
# ============================================================================

class TestNavigationControls:
    """Test camera navigation."""
    
    def test_creation(self):
        """Test creating navigation controls."""
        nav = NavigationControls()
        assert nav.camera_speed == 10.0
        assert nav.rotation_speed == 5.0
    
    def test_key_events(self):
        """Test key press events."""
        nav = NavigationControls()
        
        nav.on_key_down('w')
        nav.on_key_down('d')
        
        movement = nav.get_movement_vector()
        assert movement[0] > 0  # d pressed
        assert movement[1] > 0  # w pressed
    
    def test_mouse_drag(self):
        """Test mouse drag event."""
        nav = NavigationControls()
        
        rotation = nav.on_mouse_drag(10.0, 5.0)
        
        assert 'yaw' in rotation
        assert 'pitch' in rotation
        assert rotation['yaw'] == 10.0 * nav.rotation_speed
        assert rotation['pitch'] == 5.0 * nav.rotation_speed
    
    def test_mouse_scroll(self):
        """Test mouse scroll event."""
        nav = NavigationControls()
        
        zoom = nav.on_mouse_scroll(1.0)
        assert 0 < zoom < 1.0
        
        zoom = nav.on_mouse_scroll(-1.0)
        assert zoom > 1.0
    
    def test_movement_vector(self):
        """Test movement vector from keys."""
        nav = NavigationControls()
        
        nav.on_key_down('w')
        nav.on_key_down('d')
        nav.on_key_down('e')
        
        x, y, z = nav.get_movement_vector()
        
        assert x > 0  # d
        assert y > 0  # w
        assert z > 0  # e
    
    def test_callback_registration(self):
        """Test callback registration."""
        nav = NavigationControls()
        
        callback = Mock()
        nav.register_callback(callback)
        nav.on_key_down('a')
        
        callback.assert_called()


# ============================================================================
# InteractiveMap Tests
# ============================================================================

class TestInteractiveMap:
    """Test interactive map interface."""
    
    def test_creation(self):
        """Test creating interactive map."""
        map_widget = InteractiveMap()
        
        assert map_widget.is_active() is False
        assert map_widget.layer_toggle is not None
        assert map_widget.statistics is not None
    
    def test_activation(self):
        """Test map activation."""
        map_widget = InteractiveMap()
        
        assert map_widget.is_active() is False
        
        map_widget.activate()
        assert map_widget.is_active() is True
        
        map_widget.deactivate()
        assert map_widget.is_active() is False
    
    def test_setup(self):
        """Test setting up with renderer."""
        map_widget = InteractiveMap()
        
        mock_renderer = Mock()
        mock_renderer.layers = {
            'bathymetry': Mock(),
            'anomalies': Mock(),
            'mosaic': Mock(),
        }
        
        mock_stream = Mock()
        
        map_widget.setup(mock_renderer, mock_stream)
        
        layers = map_widget.layer_toggle.get_all_layers()
        assert 'bathymetry' in layers
        assert 'anomalies' in layers
    
    def test_update(self):
        """Test map update."""
        map_widget = InteractiveMap()
        
        mock_renderer = Mock()
        mock_renderer.get_stats.return_value = {
            'fps': 60.0,
            'frame_time_ms': 16.67,
            'vertices_rendered': 5000,
        }
        mock_renderer.camera = Mock(
            position=(0, 0, 50),
            target=(0, 0, 0),
            fov=60.0,
        )
        mock_renderer.layers = {}
        
        map_widget.setup(mock_renderer, None)
        map_widget.activate()
        
        state = map_widget.update()
        
        assert 'timestamp' in state
        assert 'statistics' in state
        assert state['statistics']['fps'] == 60.0
    
    def test_layer_toggle_handler(self):
        """Test layer toggle handling."""
        map_widget = InteractiveMap()
        
        mock_renderer = Mock()
        mock_renderer.layers = {'bathymetry': Mock()}
        
        map_widget.setup(mock_renderer, None)
        map_widget.layer_toggle.add_layer('bathymetry', visible=True)
        
        result = map_widget.handle_layer_toggle('bathymetry')
        
        assert result is False  # Was toggled from True to False
        mock_renderer.set_layer_visibility.assert_called_with('bathymetry', False)
    
    def test_camera_controls(self):
        """Test camera control handlers."""
        map_widget = InteractiveMap()
        
        mock_renderer = Mock()
        mock_renderer.layers = {}
        map_widget.setup(mock_renderer, None)
        
        # Test pan
        map_widget.handle_camera_pan(10.0, 5.0)
        mock_renderer.rotate_camera.assert_called()
        
        # Test zoom
        map_widget.handle_camera_zoom(1.0)
        mock_renderer.zoom_camera.assert_called()
    
    def test_snapshot_export(self):
        """Test snapshot export."""
        map_widget = InteractiveMap()
        
        filepath = map_widget.handle_snapshot_export()
        
        assert "outputs" in filepath
        assert ".png" in filepath
    
    def test_video_export(self):
        """Test video export."""
        map_widget = InteractiveMap()
        
        start_path = map_widget.handle_video_export_start()
        assert ".webm" in start_path
        
        stop_path = map_widget.handle_video_export_stop()
        assert stop_path == start_path
    
    def test_get_ui_state(self):
        """Test getting UI state."""
        map_widget = InteractiveMap()
        map_widget.activate()
        map_widget.layer_toggle.add_layer("bath", visible=True)
        
        ui_state = map_widget.get_ui_state()
        
        assert ui_state['map_active'] is True
        assert 'layers' in ui_state
        assert 'statistics' in ui_state
        assert 'settings' in ui_state
    
    def test_to_dict(self):
        """Test serialization."""
        map_widget = InteractiveMap(MapSettings(width=800, height=600))
        map_widget.activate()
        
        data = map_widget.to_dict()
        
        assert data['type'] == 'interactive_map'
        assert data['active'] is True
        assert data['settings']['width'] == 800
        assert data['settings']['height'] == 600


# ============================================================================
# Integration Tests
# ============================================================================

class TestInteractiveMapIntegration:
    """Integration tests for interactive map."""
    
    def test_complete_workflow(self):
        """Test complete interactive map workflow."""
        # Create map
        map_widget = InteractiveMap(MapSettings(width=1024, height=768))
        
        # Setup with mock renderer
        mock_renderer = Mock()
        mock_renderer.layers = {
            'bathymetry': Mock(),
            'anomalies': Mock(),
            'mosaic': Mock(),
        }
        mock_renderer.get_stats.return_value = {
            'fps': 60.0,
            'frame_time_ms': 16.67,
            'vertices_rendered': 5000,
        }
        mock_renderer.camera = Mock(
            position=(0, 0, 50),
            target=(0, 0, 0),
            fov=60.0,
        )
        
        mock_stream = Mock()
        mock_stream.get_stats.return_value = {
            'samples_per_second': 10000,
            'anomalies_detected': 5,
        }
        
        map_widget.setup(mock_renderer, mock_stream)
        
        # Activate
        map_widget.activate()
        assert map_widget.is_active()
        
        # Interact with layers
        map_widget.handle_layer_toggle('bathymetry')
        layers = map_widget.layer_toggle.get_all_layers()
        assert layers['bathymetry'] is False
        
        # Control camera
        map_widget.handle_camera_pan(10.0, 5.0)
        map_widget.handle_camera_zoom(1.0)
        
        # Export
        snap_path = map_widget.handle_snapshot_export()
        assert snap_path is not None
        
        # Update and check state
        state = map_widget.update()
        assert state['statistics']['anomalies_detected'] == 5
        
        ui_state = map_widget.get_ui_state()
        assert ui_state['map_active'] is True
    
    def test_multi_layer_interaction(self):
        """Test interaction with multiple layers."""
        map_widget = InteractiveMap()
        
        # Add multiple layers
        map_widget.layer_toggle.add_layer("bath", visible=True)
        map_widget.layer_toggle.add_layer("anom", visible=True)
        map_widget.layer_toggle.add_layer("mosaic", visible=True)
        
        # Toggle different combinations
        map_widget.layer_toggle.toggle_layer("bath")
        map_widget.layer_toggle.toggle_layer("anom")
        
        visible = map_widget.layer_toggle.get_visible_layers()
        assert "bath" not in visible
        assert "anom" not in visible
        assert "mosaic" in visible
    
    def test_export_workflow(self):
        """Test complete export workflow."""
        map_widget = InteractiveMap()
        
        # Export snapshot
        snap1 = map_widget.handle_snapshot_export()
        snap2 = map_widget.handle_snapshot_export()
        
        # Start video
        vid_path = map_widget.handle_video_export_start()
        
        # Stop video
        vid_completed = map_widget.handle_video_export_stop()
        
        # Check history
        history = map_widget.exporter.get_export_history()
        assert len(history) == 3  # 2 snapshots + 1 video


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
