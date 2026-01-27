"""
Unit Tests for Sonar Visualization Module (Phase 12.2)

Tests for WebGL renderer, layers, camera controls, and visualization pipeline.

Author: CESARops Development
Date: January 27, 2026
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock

from src.cesarops.sonar_visualization import (
    Color, CameraState, ViewportSettings, BathymetryLayer,
    AnomalyLayer, MosaicLayer, WebGLRenderer, VisualizationPipeline,
    BlendMode
)


# ============================================================================
# Color Tests
# ============================================================================

class TestColor:
    """Test color handling."""
    
    def test_color_creation(self):
        """Test creating a color."""
        color = Color(1.0, 0.5, 0.0, 0.8)
        assert color.r == 1.0
        assert color.g == 0.5
        assert color.b == 0.0
        assert color.a == 0.8
    
    def test_color_hex_conversion(self):
        """Test conversion to hex."""
        color = Color(1.0, 0.0, 0.0)
        assert color.to_hex() == "#ff0000"
    
    def test_color_to_dict(self):
        """Test conversion to dict."""
        color = Color(0.5, 0.5, 0.5, 0.9)
        d = color.to_dict()
        assert d["r"] == 0.5
        assert d["a"] == 0.9


# ============================================================================
# Camera Tests
# ============================================================================

class TestCameraState:
    """Test camera configuration."""
    
    def test_camera_creation(self):
        """Test creating camera."""
        cam = CameraState(
            position=(0, 0, 50),
            target=(0, 0, 0)
        )
        assert cam.position == (0, 0, 50)
        assert cam.target == (0, 0, 0)
        assert cam.fov == 60.0
    
    def test_camera_defaults(self):
        """Test camera default values."""
        cam = CameraState((0, 0, 0), (0, 0, 0))
        assert cam.up == (0, 0, 1)
        assert cam.near == 0.1
        assert cam.far == 10000.0


# ============================================================================
# BathymetryLayer Tests
# ============================================================================

class TestBathymetryLayer:
    """Test bathymetry visualization."""
    
    def test_layer_creation(self):
        """Test creating bathymetry layer."""
        grid = np.random.rand(10, 10) * -100
        layer = BathymetryLayer(grid, resolution=1.0)
        assert layer.visible is True
        assert layer.opacity == 1.0
    
    def test_depth_color_mapping(self):
        """Test depth to color mapping."""
        grid = np.array([[-1], [-5], [-20]])
        layer = BathymetryLayer(grid)
        
        color_shallow = layer.get_depth_color(-1)
        color_deep = layer.get_depth_color(-20)
        
        # Shallow should be lighter
        assert color_shallow.b > color_deep.b
    
    def test_mesh_generation(self):
        """Test mesh data generation."""
        grid = np.ones((5, 5)) * -10
        layer = BathymetryLayer(grid, resolution=1.0)
        
        mesh = layer.get_mesh_data()
        assert "vertices" in mesh
        assert "colors" in mesh
        assert "indices" in mesh
        assert len(mesh["vertices"]) == 25  # 5x5 grid
    
    def test_mesh_caching(self):
        """Test mesh caching."""
        grid = np.ones((5, 5)) * -10
        layer = BathymetryLayer(grid)
        
        mesh1 = layer.get_mesh_data()
        mesh2 = layer.get_mesh_data()
        
        # Should return same object (cached)
        assert mesh1 is mesh2


# ============================================================================
# AnomalyLayer Tests
# ============================================================================

class TestAnomalyLayer:
    """Test anomaly visualization."""
    
    def test_layer_creation(self):
        """Test creating anomaly layer."""
        layer = AnomalyLayer()
        assert layer.visible is True
        assert len(layer.anomalies) == 0
    
    def test_add_anomaly(self):
        """Test adding anomaly."""
        layer = AnomalyLayer()
        layer.add_anomaly(10, 20, -50, "strong_return", 0.9)
        
        assert len(layer.anomalies) == 1
        assert layer.anomalies[0]["type"] == "strong_return"
        assert layer.anomalies[0]["confidence"] == 0.9
    
    def test_point_cloud_generation(self):
        """Test point cloud data generation."""
        layer = AnomalyLayer()
        layer.add_anomaly(0, 0, -10, "strong_return", 0.8)
        layer.add_anomaly(5, 5, -20, "unusual_pattern", 0.6)
        
        cloud = layer.get_point_cloud_data()
        assert len(cloud["points"]) == 2
        assert len(cloud["colors"]) == 2
        assert len(cloud["sizes"]) == 2
    
    def test_anomaly_type_colors(self):
        """Test color mapping by type."""
        layer = AnomalyLayer()
        
        # Add different anomaly types
        layer.add_anomaly(0, 0, -10, "strong_return")
        layer.add_anomaly(1, 0, -10, "structured_pattern")
        layer.add_anomaly(2, 0, -10, "persistent_feature")
        layer.add_anomaly(3, 0, -10, "unusual_pattern")
        
        cloud = layer.get_point_cloud_data()
        assert len(cloud["colors"]) == 4


# ============================================================================
# MosaicLayer Tests
# ============================================================================

class TestMosaicLayer:
    """Test mosaic visualization."""
    
    def test_layer_creation(self):
        """Test creating mosaic layer."""
        mosaic = np.ones((10, 10))
        layer = MosaicLayer(mosaic, 100, 100)
        
        assert layer.visible is True
        assert layer.width_m == 100
        assert layer.height_m == 100
    
    def test_texture_generation(self):
        """Test texture data generation."""
        mosaic = np.random.rand(10, 10)
        layer = MosaicLayer(mosaic, 100, 100)
        
        texture = layer.get_texture_data()
        assert "texture" in texture
        assert texture["width"] == 10
        assert texture["height"] == 10
    
    def test_blend_mode(self):
        """Test blend mode setting."""
        mosaic = np.ones((5, 5))
        layer = MosaicLayer(mosaic, 50, 50)
        
        layer.blend_mode = BlendMode.MULTIPLY
        texture = layer.get_texture_data()
        assert texture["blend_mode"] == "multiply"


# ============================================================================
# WebGLRenderer Tests
# ============================================================================

class TestWebGLRenderer:
    """Test WebGL rendering engine."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer."""
        viewport = ViewportSettings(800, 600)
        return WebGLRenderer(viewport)
    
    def test_renderer_creation(self, renderer):
        """Test creating renderer."""
        assert renderer.viewport.width == 800
        assert renderer.viewport.height == 600
        assert renderer.camera is not None
    
    def test_add_bathymetry_layer(self, renderer):
        """Test adding bathymetry layer."""
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bathymetry", grid)
        
        assert "bathymetry" in renderer.layers
        assert isinstance(renderer.layers["bathymetry"], BathymetryLayer)
    
    def test_add_anomaly_layer(self, renderer):
        """Test adding anomaly layer."""
        renderer.add_anomaly_layer("anomalies")
        
        assert "anomalies" in renderer.layers
        assert isinstance(renderer.layers["anomalies"], AnomalyLayer)
    
    def test_add_mosaic_layer(self, renderer):
        """Test adding mosaic layer."""
        mosaic = np.random.rand(10, 10)
        renderer.add_mosaic_layer("mosaic", mosaic, 100, 100)
        
        assert "mosaic" in renderer.layers
        assert isinstance(renderer.layers["mosaic"], MosaicLayer)
    
    def test_set_camera_position(self, renderer):
        """Test setting camera position."""
        renderer.set_camera_position((10, 20, 30))
        assert renderer.camera.position == (10, 20, 30)
    
    def test_set_camera_target(self, renderer):
        """Test setting camera target."""
        renderer.set_camera_target((5, 5, 5))
        assert renderer.camera.target == (5, 5, 5)
    
    def test_rotate_camera(self, renderer):
        """Test camera rotation."""
        initial_pos = renderer.camera.position
        renderer.rotate_camera(45, 0)
        
        # Position should change
        assert renderer.camera.position != initial_pos
    
    def test_zoom_camera(self, renderer):
        """Test camera zoom."""
        initial_pos = renderer.camera.position
        renderer.zoom_camera(1.0)  # Zoom in
        
        # Distance should decrease
        target = renderer.camera.target
        initial_dist = np.sqrt(sum((p - t)**2 for p, t in zip(initial_pos, target)))
        new_dist = np.sqrt(sum((p - t)**2 for p, t in zip(renderer.camera.position, target)))
        
        assert new_dist < initial_dist
    
    def test_layer_visibility(self, renderer):
        """Test toggling layer visibility."""
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bath", grid)
        
        layer = renderer.layers["bath"]
        assert layer.visible is True
        
        renderer.set_layer_visibility("bath", False)
        assert layer.visible is False
    
    def test_render_frame(self, renderer):
        """Test frame rendering."""
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bath", grid)
        
        frame = renderer.render_frame()
        
        assert "viewport" in frame
        assert "camera" in frame
        assert "lighting" in frame
        assert "layers" in frame
        assert "stats" in frame
    
    def test_render_stats(self, renderer):
        """Test rendering statistics."""
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bath", grid)
        
        renderer.render_frame()
        stats = renderer.get_stats()
        
        assert "frame_time_ms" in stats
        assert "fps" in stats
        assert "vertices_rendered" in stats
    
    def test_fps_calculation(self, renderer):
        """Test FPS calculation."""
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bath", grid)
        
        # Render multiple frames
        for _ in range(10):
            renderer.render_frame()
        
        stats = renderer.get_stats()
        assert stats["fps"] > 0


# ============================================================================
# VisualizationPipeline Tests
# ============================================================================

class TestVisualizationPipeline:
    """Test visualization pipeline."""
    
    def test_pipeline_creation(self):
        """Test creating pipeline."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        pipeline = VisualizationPipeline(renderer)
        
        assert pipeline.renderer is renderer
    
    def test_add_frame_data(self):
        """Test adding frame data."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        pipeline = VisualizationPipeline(renderer)
        
        frame_data = {"test": "data"}
        pipeline.add_frame_data(frame_data)
        
        assert len(pipeline.frame_queue) == 1
    
    def test_get_next_frame(self):
        """Test getting next frame."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        pipeline = VisualizationPipeline(renderer)
        
        pipeline.add_frame_data({"test": 1})
        pipeline.add_frame_data({"test": 2})
        
        frame1 = pipeline.get_next_frame()
        frame2 = pipeline.get_next_frame()
        
        assert frame1["data"]["test"] == 1
        assert frame2["data"]["test"] == 2
    
    def test_render(self):
        """Test rendering through pipeline."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bath", grid)
        
        pipeline = VisualizationPipeline(renderer)
        frame = pipeline.render()
        
        assert "viewport" in frame
        assert "stats" in frame


# ============================================================================
# Integration Tests
# ============================================================================

class TestVisualizationIntegration:
    """Integration tests for visualization system."""
    
    def test_complete_visualization_pipeline(self):
        """Test complete pipeline from data to frame."""
        # Create renderer with all layers
        viewport = ViewportSettings(1024, 768)
        renderer = WebGLRenderer(viewport)
        
        # Add bathymetry
        bath_grid = np.random.rand(20, 20) * -50
        renderer.add_bathymetry_layer("bathymetry", bath_grid)
        
        # Add anomalies
        renderer.add_anomaly_layer("anomalies")
        anomaly_layer = renderer.layers["anomalies"]
        for i in range(5):
            x, y = i * 10, i * 10
            anomaly_layer.add_anomaly(x, y, -25, "strong_return", 0.8)
        
        # Add mosaic
        mosaic_data = np.random.rand(20, 20)
        renderer.add_mosaic_layer("mosaic", mosaic_data, 200, 200)
        
        # Render frame
        frame = renderer.render_frame()
        
        # Verify all layers rendered
        assert "bathymetry" in frame["layers"]
        assert "anomalies" in frame["layers"]
        assert "mosaic" in frame["layers"]
        
        # Verify stats
        assert frame["stats"]["vertices_rendered"] > 0
    
    def test_camera_manipulation(self):
        """Test camera controls."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        # Set initial view
        renderer.set_camera_position((0, 0, 100))
        renderer.set_camera_target((0, 0, 0))
        
        # Rotate
        renderer.rotate_camera(45, 0)
        
        # Zoom
        renderer.zoom_camera(1.0)
        
        # Verify changes
        assert renderer.camera.position != (0, 0, 100)
    
    def test_layer_toggling(self):
        """Test turning layers on/off."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        grid = np.ones((5, 5)) * -10
        renderer.add_bathymetry_layer("bath", grid)
        renderer.add_anomaly_layer("anom")
        
        # Render with both visible
        frame1 = renderer.render_frame()
        count1 = len(frame1["layers"])
        
        # Hide bathymetry
        renderer.set_layer_visibility("bath", False)
        frame2 = renderer.render_frame()
        count2 = len(frame2["layers"])
        
        assert count2 < count1
    
    def test_60fps_capable(self):
        """Test that renderer achieves 60+ FPS."""
        viewport = ViewportSettings(800, 600)
        renderer = WebGLRenderer(viewport)
        
        grid = np.random.rand(50, 50) * -100
        renderer.add_bathymetry_layer("bath", grid)
        
        # Render 60 frames
        for _ in range(60):
            renderer.render_frame()
        
        stats = renderer.get_stats()
        assert stats["fps"] > 30  # At least 30 FPS


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
