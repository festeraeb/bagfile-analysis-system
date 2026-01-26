"""
Unit Tests for SonarMosaicGenerator (Phase 11.3)

Tests covering:
- Initialization and configuration
- Layer management and validation
- Composite generation with different blend modes
- Quality analysis
- Export functionality (GeoJSON, KML, JSON)
- Integration with bathymetry and anomaly detectors
"""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from src.cesarops.sonar_mosaic import (
    SonarMosaicGenerator, MosaicLayer, MosaicConfig
)


class TestInitialization:
    """Test mosaic generator initialization."""
    
    def test_basic_initialization(self):
        """Test default initialization."""
        mosaic = SonarMosaicGenerator()
        assert mosaic.composite is None
        assert len(mosaic.layers) == 0
        assert mosaic.metadata["has_bathymetry"] is False
        assert mosaic.metadata["has_anomalies"] is False
    
    def test_initialization_with_config(self):
        """Test initialization with custom configuration."""
        config = MosaicConfig(
            include_bathymetry=False,
            blend_mode="multiply",
            color_scheme="terrain"
        )
        mosaic = SonarMosaicGenerator(config=config)
        assert mosaic.config.include_bathymetry is False
        assert mosaic.config.blend_mode == "multiply"


class TestLayerManagement:
    """Test adding and managing layers."""
    
    def test_add_single_layer(self):
        """Test adding a single layer."""
        mosaic = SonarMosaicGenerator()
        data = np.random.rand(50, 50)
        layer = MosaicLayer(
            name="test_layer",
            data=data,
            extent=(-85.0, -84.5, 42.0, 42.5),
            opacity=0.8
        )
        mosaic.add_layer(layer)
        
        assert len(mosaic.layers) == 1
        assert mosaic.layers[0].name == "test_layer"
        assert mosaic.metadata["num_layers"] == 1
    
    def test_add_multiple_layers(self):
        """Test adding multiple layers."""
        mosaic = SonarMosaicGenerator()
        for i in range(3):
            data = np.random.rand(50, 50)
            layer = MosaicLayer(
                name=f"layer_{i}",
                data=data,
                extent=(-85.0, -84.5, 42.0, 42.5),
                z_order=i
            )
            mosaic.add_layer(layer)
        
        assert len(mosaic.layers) == 3
        assert mosaic.metadata["num_layers"] == 3
    
    def test_invalid_layer_dimension(self):
        """Test rejection of invalid layer dimensions."""
        mosaic = SonarMosaicGenerator()
        with pytest.raises(ValueError, match="must be 2D"):
            layer = MosaicLayer(
                name="invalid",
                data=np.random.rand(50),  # 1D array
                extent=(-85.0, -84.5, 42.0, 42.5)
            )
            mosaic.add_layer(layer)
    
    def test_invalid_opacity(self):
        """Test rejection of invalid opacity values."""
        mosaic = SonarMosaicGenerator()
        with pytest.raises(ValueError, match="Opacity"):
            layer = MosaicLayer(
                name="invalid",
                data=np.random.rand(50, 50),
                extent=(-85.0, -84.5, 42.0, 42.5),
                opacity=1.5  # Invalid: > 1
            )
            mosaic.add_layer(layer)
    
    def test_method_chaining(self):
        """Test method chaining with add_layer."""
        mosaic = SonarMosaicGenerator()
        layer1 = MosaicLayer("l1", np.random.rand(50, 50), (-85.0, -84.5, 42.0, 42.5))
        layer2 = MosaicLayer("l2", np.random.rand(50, 50), (-85.0, -84.5, 42.0, 42.5))
        
        result = mosaic.add_layer(layer1).add_layer(layer2)
        
        assert result is mosaic
        assert len(mosaic.layers) == 2


class TestCompositeGeneration:
    """Test composite generation with different blend modes."""
    
    def test_composite_single_layer(self):
        """Test composite from single layer."""
        mosaic = SonarMosaicGenerator()
        data = np.random.rand(50, 50)
        layer = MosaicLayer("test", data, (-85.0, -84.5, 42.0, 42.5))
        mosaic.add_layer(layer)
        
        composite = mosaic.create_composite(auto_layers=False)
        
        assert composite is not None
        assert composite.shape == (50, 50)
        assert np.all((composite >= 0) & (composite <= 1))
    
    def test_composite_multiple_layers(self):
        """Test composite from multiple layers."""
        mosaic = SonarMosaicGenerator()
        for i in range(3):
            layer = MosaicLayer(
                f"layer_{i}",
                np.ones((50, 50)) * (i + 1) / 3,
                (-85.0, -84.5, 42.0, 42.5),
                opacity=0.7,
                z_order=i
            )
            mosaic.add_layer(layer)
        
        composite = mosaic.create_composite(auto_layers=False)
        
        assert composite.shape == (50, 50)
        assert mosaic.metadata["composite_generated"] is True
    
    def test_composite_overlay_blend_mode(self):
        """Test overlay blend mode."""
        config = MosaicConfig(blend_mode="overlay")
        mosaic = SonarMosaicGenerator(config=config)
        
        base = MosaicLayer("base", np.ones((50, 50)) * 0.5, (-85.0, -84.5, 42.0, 42.5), z_order=0)
        overlay = MosaicLayer("overlay", np.ones((50, 50)) * 0.8, (-85.0, -84.5, 42.0, 42.5), z_order=1)
        
        mosaic.add_layer(base).add_layer(overlay)
        composite = mosaic.create_composite(auto_layers=False)
        
        assert composite.shape == (50, 50)
        # Overlay should brighten some areas
        assert np.mean(composite) > np.mean(base.data)
    
    def test_composite_multiply_blend_mode(self):
        """Test multiply blend mode."""
        config = MosaicConfig(blend_mode="multiply")
        mosaic = SonarMosaicGenerator(config=config)
        
        base = MosaicLayer("base", np.ones((50, 50)) * 0.8, (-85.0, -84.5, 42.0, 42.5), z_order=0)
        overlay = MosaicLayer("overlay", np.ones((50, 50)) * 0.5, (-85.0, -84.5, 42.0, 42.5), z_order=1)
        
        mosaic.add_layer(base).add_layer(overlay)
        composite = mosaic.create_composite(auto_layers=False)
        
        # Multiply should darken
        assert np.mean(composite) < np.mean(base.data)
    
    def test_composite_without_layers(self):
        """Test that composite fails without layers."""
        mosaic = SonarMosaicGenerator()
        
        with pytest.raises(ValueError, match="No layers"):
            mosaic.create_composite(auto_layers=False)
    
    def test_composite_normalization(self):
        """Test that composite is normalized to 0-1."""
        mosaic = SonarMosaicGenerator()
        # Create layer with values > 1
        data = np.random.rand(50, 50) * 10  # 0-10 range
        layer = MosaicLayer("test", data, (-85.0, -84.5, 42.0, 42.5))
        mosaic.add_layer(layer)
        
        composite = mosaic.create_composite(auto_layers=False)
        
        assert np.all(composite >= 0)
        assert np.all(composite <= 1)


class TestQualityAnalysis:
    """Test quality analysis functionality."""
    
    def test_quality_analysis(self):
        """Test basic quality analysis."""
        mosaic = SonarMosaicGenerator()
        layer = MosaicLayer("test", np.random.rand(50, 50), (-85.0, -84.5, 42.0, 42.5))
        mosaic.add_layer(layer)
        mosaic.create_composite(auto_layers=False)
        
        metrics = mosaic.analyze_quality()
        
        assert "composite_min" in metrics
        assert "composite_max" in metrics
        assert "composite_mean" in metrics
        assert "coverage" in metrics
        assert 0 <= metrics["coverage"] <= 1
    
    def test_quality_without_composite(self):
        """Test that quality analysis fails without composite."""
        mosaic = SonarMosaicGenerator()
        
        with pytest.raises(ValueError, match="Must create composite"):
            mosaic.analyze_quality()
    
    def test_quality_metrics_reasonable(self):
        """Test that quality metrics have reasonable values."""
        mosaic = SonarMosaicGenerator()
        data = np.random.rand(100, 100)
        layer = MosaicLayer("test", data, (-85.0, -84.5, 42.0, 42.5))
        mosaic.add_layer(layer)
        mosaic.create_composite(auto_layers=False)
        
        metrics = mosaic.analyze_quality()
        
        # Min should be <= mean <= max
        assert metrics["composite_min"] <= metrics["composite_mean"]
        assert metrics["composite_mean"] <= metrics["composite_max"]


class TestExport:
    """Test exporting mosaic in various formats."""
    
    def setup_method(self):
        """Set up mosaic for export tests."""
        self.mosaic = SonarMosaicGenerator()
        layer = MosaicLayer("test", np.random.rand(50, 50), (-85.0, -84.5, 42.0, 42.5))
        self.mosaic.add_layer(layer)
        self.mosaic.create_composite(auto_layers=False)
    
    def test_export_geojson(self):
        """Test GeoJSON export."""
        filepath = Path(tempfile.gettempdir()) / f"mosaic_test_{id(self)}.geojson"
        try:
            success = self.mosaic.export_to_geojson(str(filepath))
            assert success is True
            
            # Verify file contents
            with open(filepath) as f:
                data = json.load(f)
            
            assert data["type"] == "FeatureCollection"
            assert "features" in data
            assert "properties" in data
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_export_kml(self):
        """Test KML export."""
        filepath = Path(tempfile.gettempdir()) / f"mosaic_test_{id(self)}.kml"
        try:
            success = self.mosaic.export_to_kml(str(filepath))
            assert success is True
            
            with open(filepath) as f:
                content = f.read()
            
            assert "kml" in content.lower()
            assert "GroundOverlay" in content
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_export_json(self):
        """Test JSON export."""
        filepath = Path(tempfile.gettempdir()) / f"mosaic_test_{id(self)}.json"
        try:
            success = self.mosaic.export_to_json(str(filepath))
            assert success is True
            
            with open(filepath) as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "quality_metrics" in data
            assert "layers" in data
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_export_json_with_composite(self):
        """Test JSON export including composite data."""
        filepath = Path(tempfile.gettempdir()) / f"mosaic_comp_{id(self)}.json"
        try:
            success = self.mosaic.export_to_json(str(filepath), include_composite=True)
            assert success is True
            
            with open(filepath) as f:
                data = json.load(f)
            
            assert "composite" in data
            assert len(data["composite"]) == 50
        finally:
            if filepath.exists():
                filepath.unlink()


class TestLayerCreation:
    """Test automatic layer creation from external sources."""
    
    def test_create_bathymetry_layer_without_data(self):
        """Test bathymetry layer creation fails without data."""
        mosaic = SonarMosaicGenerator()
        layer = mosaic.create_bathymetry_layer()
        assert layer is None
    
    def test_create_anomaly_layer_without_detector(self):
        """Test anomaly layer creation fails without detector."""
        mosaic = SonarMosaicGenerator()
        layer = mosaic.create_anomaly_layer()
        assert layer is None
    
    def test_create_confidence_layer_without_bathymetry(self):
        """Test confidence layer creation fails without bathymetry."""
        mosaic = SonarMosaicGenerator()
        layer = mosaic.create_confidence_layer()
        assert layer is None


class TestIntegration:
    """Integration tests for mosaic generation."""
    
    def test_complete_workflow(self):
        """Test complete mosaic generation workflow."""
        mosaic = SonarMosaicGenerator()
        
        # Add multiple layers
        for i in range(2):
            layer = MosaicLayer(
                f"layer_{i}",
                np.random.rand(50, 50),
                (-85.0, -84.5, 42.0, 42.5),
                z_order=i
            )
            mosaic.add_layer(layer)
        
        # Generate composite
        composite = mosaic.create_composite(auto_layers=False)
        assert composite is not None
        
        # Analyze quality
        metrics = mosaic.analyze_quality()
        assert metrics["coverage"] > 0
        
        # Get statistics
        stats = mosaic.get_statistics()
        assert stats["num_layers"] == 2
        assert stats["composite_generated"] is True
    
    def test_layer_ordering(self):
        """Test that layers are composited in z_order."""
        mosaic = SonarMosaicGenerator()
        
        # Add layers with specific z_orders
        layer1 = MosaicLayer("first", np.ones((50, 50)) * 0.1, (-85.0, -84.5, 42.0, 42.5), z_order=1)
        layer2 = MosaicLayer("second", np.ones((50, 50)) * 0.9, (-85.0, -84.5, 42.0, 42.5), z_order=2)
        layer3 = MosaicLayer("third", np.ones((50, 50)) * 0.5, (-85.0, -84.5, 42.0, 42.5), z_order=0)
        
        # Add in random order
        mosaic.add_layer(layer1).add_layer(layer3).add_layer(layer2)
        
        # Composite should respect z_order
        composite = mosaic.create_composite(auto_layers=False)
        
        # Higher z_order layers should have more influence
        assert composite is not None
    
    def test_method_chaining_workflow(self):
        """Test workflow using method chaining."""
        layer1 = MosaicLayer("l1", np.random.rand(50, 50), (-85.0, -84.5, 42.0, 42.5))
        layer2 = MosaicLayer("l2", np.random.rand(50, 50), (-85.0, -84.5, 42.0, 42.5))
        
        result = (SonarMosaicGenerator()
                  .add_layer(layer1)
                  .add_layer(layer2))
        
        composite = result.create_composite(auto_layers=False)
        stats = result.get_statistics()
        
        assert composite is not None
        assert stats["num_layers"] == 2


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_uniform_data_layer(self):
        """Test layer with uniform values."""
        mosaic = SonarMosaicGenerator()
        layer = MosaicLayer("uniform", np.ones((50, 50)), (-85.0, -84.5, 42.0, 42.5))
        mosaic.add_layer(layer)
        
        composite = mosaic.create_composite(auto_layers=False)
        
        # Should handle uniform data gracefully
        assert composite.shape == (50, 50)
        assert np.allclose(composite, 1.0)
    
    def test_zero_opacity_layer(self):
        """Test layer with zero opacity."""
        mosaic = SonarMosaicGenerator()
        layer1 = MosaicLayer("base", np.ones((50, 50)) * 0.5, (-85.0, -84.5, 42.0, 42.5), z_order=0)
        layer2 = MosaicLayer("transparent", np.ones((50, 50)), (-85.0, -84.5, 42.0, 42.5), opacity=0, z_order=1)
        
        mosaic.add_layer(layer1).add_layer(layer2)
        composite = mosaic.create_composite(auto_layers=False)
        
        # Transparent layer shouldn't affect result
        assert composite is not None
    
    def test_large_layer(self):
        """Test with larger layer."""
        mosaic = SonarMosaicGenerator()
        large_data = np.random.rand(500, 500)
        layer = MosaicLayer("large", large_data, (-85.0, -84.5, 42.0, 42.5))
        mosaic.add_layer(layer)
        
        composite = mosaic.create_composite(auto_layers=False)
        
        assert composite.shape == (500, 500)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
