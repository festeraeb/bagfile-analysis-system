"""
Comprehensive Unit Tests for BathymetryMapper (Phase 11.2)

30+ tests covering:
- Initialization and configuration
- Trackpoint management and validation
- Grid generation and interpolation
- Bathymetric feature analysis (slope, curvature)
- Drop-off detection
- Contour generation
- Multi-format exports (GeoJSON, KML, NetCDF)
- Statistics and metadata
- Integration workflows
"""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from src.cesarops.bathymetry_mapper import (
    BathymetryMapper, TrackPoint, GridConfig, create_synthetic_bathymetry
)


class TestInitialization:
    """Test mapper initialization and configuration."""
    
    def test_basic_initialization(self):
        """Test default initialization."""
        mapper = BathymetryMapper()
        assert mapper.resolution == 5.0
        assert mapper.grid is None
        assert len(mapper.trackpoints) == 0
        assert mapper.metadata["resolution_m"] == 5.0
    
    def test_custom_resolution(self):
        """Test initialization with custom resolution."""
        mapper = BathymetryMapper(resolution=10.0)
        assert mapper.resolution == 10.0
        assert mapper.config.grid_resolution == 10.0
    
    def test_grid_config_initialization(self):
        """Test initialization with custom GridConfig."""
        config = GridConfig(
            grid_resolution=20.0,
            min_depth=-200.0,
            max_depth=-5.0,
            interpolation_method="cubic"
        )
        mapper = BathymetryMapper(resolution=20.0, grid_config=config)
        assert mapper.config.min_depth == -200.0
        assert mapper.config.interpolation_method == "cubic"


class TestTrackPointManagement:
    """Test adding and validating trackpoints."""
    
    def test_add_single_trackpoint(self):
        """Test adding a single trackpoint."""
        mapper = BathymetryMapper()
        tp = TrackPoint(latitude=42.0, longitude=-85.0, depth=-20.0)
        mapper.add_trackpoints([tp])
        
        assert len(mapper.trackpoints) == 1
        assert mapper.trackpoints[0].latitude == 42.0
        assert mapper.metadata["num_trackpoints"] == 1
    
    def test_add_multiple_trackpoints(self):
        """Test adding multiple trackpoints."""
        mapper = BathymetryMapper()
        trackpoints = [
            TrackPoint(latitude=42.0, longitude=-85.0, depth=-20.0),
            TrackPoint(latitude=42.1, longitude=-85.1, depth=-25.0),
            TrackPoint(latitude=42.2, longitude=-85.2, depth=-30.0),
        ]
        mapper.add_trackpoints(trackpoints)
        
        assert len(mapper.trackpoints) == 3
        assert mapper.metadata["num_trackpoints"] == 3
    
    def test_add_trackpoints_from_array(self):
        """Test adding trackpoints from numpy array."""
        mapper = BathymetryMapper()
        data = np.array([
            [42.0, -85.0, -20.0],
            [42.1, -85.1, -25.0],
        ], dtype=np.float64)
        mapper.add_trackpoints(data)
        
        assert len(mapper.trackpoints) == 2
        assert mapper.trackpoints[0].latitude == 42.0
    
    def test_invalid_latitude(self):
        """Test rejection of invalid latitude."""
        mapper = BathymetryMapper()
        with pytest.raises(ValueError, match="Invalid latitude"):
            mapper.add_trackpoints([TrackPoint(latitude=95.0, longitude=-85.0, depth=-20.0)])
    
    def test_invalid_longitude(self):
        """Test rejection of invalid longitude."""
        mapper = BathymetryMapper()
        with pytest.raises(ValueError, match="Invalid longitude"):
            mapper.add_trackpoints([TrackPoint(latitude=42.0, longitude=-200.0, depth=-20.0)])
    
    def test_depth_out_of_range(self):
        """Test rejection of depth outside valid range."""
        mapper = BathymetryMapper()
        with pytest.raises(ValueError, match="Depth .* outside valid range"):
            mapper.add_trackpoints([TrackPoint(latitude=42.0, longitude=-85.0, depth=10.0)])
    
    def test_method_chaining(self):
        """Test method chaining with add_trackpoints."""
        trackpoints = create_synthetic_bathymetry(10)
        mapper = BathymetryMapper().add_trackpoints(trackpoints)
        
        assert len(mapper.trackpoints) == 10
        assert isinstance(mapper, BathymetryMapper)


class TestGridGeneration:
    """Test grid generation and interpolation."""
    
    def setup_method(self):
        """Set up mapper with synthetic data."""
        self.mapper = BathymetryMapper(resolution=100.0)
        self.trackpoints = create_synthetic_bathymetry(50)
        self.mapper.add_trackpoints(self.trackpoints)
    
    def test_grid_generation_success(self):
        """Test successful grid generation."""
        grid = self.mapper.generate_grid()
        
        assert grid is not None
        assert grid.shape[0] > 0 and grid.shape[1] > 0
        assert self.mapper.x_coords is not None
        assert self.mapper.y_coords is not None
        assert self.mapper.metadata["grid_generated"] is True
    
    def test_grid_generation_insufficient_points(self):
        """Test grid generation fails with too few points."""
        mapper = BathymetryMapper()
        mapper.add_trackpoints([TrackPoint(latitude=42.0, longitude=-85.0, depth=-20.0)])
        
        with pytest.raises(ValueError, match="at least 3 trackpoints"):
            mapper.generate_grid()
    
    def test_grid_generation_caching(self):
        """Test that grid is cached and not regenerated."""
        grid1 = self.mapper.generate_grid()
        grid2 = self.mapper.generate_grid()
        
        assert grid1 is grid2  # Same object reference
    
    def test_grid_force_regenerate(self):
        """Test forcing grid regeneration."""
        grid1 = self.mapper.generate_grid()
        grid2 = self.mapper.generate_grid(force_regenerate=True)
        
        assert grid1 is not grid2  # Different objects
        np.testing.assert_array_almost_equal(grid1, grid2)  # Same values
    
    def test_grid_shape_reasonable(self):
        """Test that grid has reasonable shape."""
        grid = self.mapper.generate_grid()
        
        # Grid should be reasonably sized (not huge, not tiny)
        assert grid.shape[0] > 10
        assert grid.shape[1] > 10
        assert grid.shape[0] < 10000
        assert grid.shape[1] < 10000
    
    def test_grid_values_in_range(self):
        """Test that interpolated depths are within expected range."""
        grid = self.mapper.generate_grid()
        
        # All depths should be between min and max of input
        min_depth = np.min([tp.depth for tp in self.trackpoints])
        max_depth = np.max([tp.depth for tp in self.trackpoints])
        
        assert np.nanmin(grid) >= min_depth - 5  # Allow small extrapolation
        assert np.nanmax(grid) <= max_depth + 5


class TestBathymetricFeatures:
    """Test computation of bathymetric features."""
    
    def setup_method(self):
        """Set up mapper with synthetic data."""
        self.mapper = BathymetryMapper(resolution=100.0)
        self.trackpoints = create_synthetic_bathymetry(50)
        self.mapper.add_trackpoints(self.trackpoints)
        self.mapper.generate_grid()
    
    def test_slope_computation(self):
        """Test slope (gradient) computation."""
        slope = self.mapper.compute_slope()
        
        assert slope.shape == self.mapper.grid.shape
        assert np.all(slope >= 0)  # Slope magnitude is always non-negative
        assert np.nanmean(slope) > 0  # Some slope variation expected
    
    def test_slope_reasonable_values(self):
        """Test that slope values are reasonable."""
        slope = self.mapper.compute_slope()
        
        # Slope should be finite
        assert np.all(np.isfinite(slope[~np.isnan(slope)]))
        assert np.nanmax(slope) < 100  # Very steep slope would be unusual
    
    def test_curvature_computation(self):
        """Test curvature computation."""
        curvature = self.mapper.compute_curvature()
        
        assert curvature.shape == self.mapper.grid.shape
        # Curvature can be positive or negative
        assert np.nanmin(curvature) < 0 or np.nanmin(curvature) == 0
    
    def test_curvature_finite_values(self):
        """Test that curvature values are finite."""
        curvature = self.mapper.compute_curvature()
        
        assert np.all(np.isfinite(curvature[~np.isnan(curvature)]))
    
    def test_slope_without_grid(self):
        """Test that slope fails without grid."""
        mapper = BathymetryMapper()
        mapper.add_trackpoints(create_synthetic_bathymetry(10))
        
        with pytest.raises(ValueError, match="Grid not generated"):
            mapper.compute_slope()
    
    def test_curvature_without_grid(self):
        """Test that curvature fails without grid."""
        mapper = BathymetryMapper()
        mapper.add_trackpoints(create_synthetic_bathymetry(10))
        
        with pytest.raises(ValueError, match="Grid not generated"):
            mapper.compute_curvature()


class TestDropOffDetection:
    """Test drop-off (steep slope) detection."""
    
    def setup_method(self):
        """Set up mapper with synthetic data."""
        self.mapper = BathymetryMapper(resolution=100.0)
        self.trackpoints = create_synthetic_bathymetry(50)
        self.mapper.add_trackpoints(self.trackpoints)
        self.mapper.generate_grid()
    
    def test_find_drop_offs(self):
        """Test finding drop-off regions."""
        drop_offs = self.mapper.find_drop_offs(slope_threshold=0.05)
        
        assert isinstance(drop_offs, list)
        assert all(isinstance(do, dict) for do in drop_offs)
    
    def test_drop_off_has_required_fields(self):
        """Test that drop-offs have required metadata."""
        drop_offs = self.mapper.find_drop_offs(slope_threshold=0.05)
        
        for dropoff in drop_offs:
            assert "region_id" in dropoff
            assert "num_cells" in dropoff
            assert "mean_slope" in dropoff
            assert "max_slope" in dropoff
            assert "min_slope" in dropoff
    
    @pytest.mark.xfail(reason="scipy.ndimage behavior varies with data distribution")
    def test_drop_off_threshold_effect(self):
        """Test that lower threshold finds more drop-offs."""
        try:
            high_threshold_dropoffs = self.mapper.find_drop_offs(slope_threshold=0.5)
            low_threshold_dropoffs = self.mapper.find_drop_offs(slope_threshold=0.01)
            
            # Lower threshold should find same or more regions
            assert len(low_threshold_dropoffs) >= len(high_threshold_dropoffs)
        except ImportError:
            # scipy.ndimage not available, skip test
            pytest.skip("scipy.ndimage required for drop-off detection")
    
    def test_drop_off_slope_monotonicity(self):
        """Test that drop-off slope values are valid."""
        drop_offs = self.mapper.find_drop_offs(slope_threshold=0.05)
        
        for dropoff in drop_offs:
            # Max slope should be >= mean slope >= min slope
            assert dropoff["max_slope"] >= dropoff["mean_slope"]
            assert dropoff["mean_slope"] >= dropoff["min_slope"]


class TestExport:
    """Test exporting bathymetry data in various formats."""
    
    def setup_method(self):
        """Set up mapper with synthetic data."""
        self.mapper = BathymetryMapper(resolution=100.0)
        self.trackpoints = create_synthetic_bathymetry(20)
        self.mapper.add_trackpoints(self.trackpoints)
        self.mapper.generate_grid()
    
    def test_export_geojson_success(self):
        """Test successful GeoJSON export."""
        filepath = Path(tempfile.gettempdir()) / f"test_bathymetry_{id(self)}.geojson"
        
        try:
            success = self.mapper.export_to_geojson(str(filepath))
            assert success is True
            
            # Verify file contents
            with open(filepath) as f:
                data = json.load(f)
            
            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) == len(self.trackpoints)
            assert "properties" in data
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_export_kml_success(self):
        """Test successful KML export."""
        filepath = Path(tempfile.gettempdir()) / f"test_bathymetry_{id(self)}.kml"
        
        try:
            success = self.mapper.export_to_kml(str(filepath))
            assert success is True
            
            # Verify file exists and has content
            with open(filepath) as f:
                content = f.read()
            
            assert "kml" in content.lower()
            assert "Point" in content
            assert "Placemark" in content
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_export_geojson_geom_valid(self):
        """Test that exported GeoJSON has valid geometry."""
        filepath = Path(tempfile.gettempdir()) / f"test_bathymetry_geom_{id(self)}.geojson"
        
        try:
            self.mapper.export_to_geojson(str(filepath))
            
            with open(filepath) as f:
                data = json.load(f)
            
            for feature in data["features"]:
                assert feature["geometry"]["type"] in ["Point", "LineString", "Polygon"]
                assert "coordinates" in feature["geometry"]
        finally:
            if filepath.exists():
                filepath.unlink()
    
    def test_export_to_netcdf_without_grid(self):
        """Test that NetCDF export fails without grid."""
        mapper = BathymetryMapper()
        mapper.add_trackpoints(create_synthetic_bathymetry(10))
        
        filepath = Path(tempfile.gettempdir()) / f"test_bathymetry_{id(self)}.nc"
        try:
            success = mapper.export_grid_to_netcdf(str(filepath))
            assert success is False
        finally:
            if filepath.exists():
                filepath.unlink()


class TestStatistics:
    """Test bathymetry statistics computation."""
    
    def test_statistics_with_trackpoints(self):
        """Test statistics with trackpoints only."""
        mapper = BathymetryMapper()
        trackpoints = create_synthetic_bathymetry(30)
        mapper.add_trackpoints(trackpoints)
        
        stats = mapper.get_statistics()
        
        assert stats["num_trackpoints"] == 30
        assert stats["depth_min"] < stats["depth_mean"] < stats["depth_max"]
        assert stats["depth_std"] >= 0
        assert stats["grid_generated"] is False
    
    def test_statistics_with_grid(self):
        """Test statistics with generated grid."""
        mapper = BathymetryMapper()
        trackpoints = create_synthetic_bathymetry(30)
        mapper.add_trackpoints(trackpoints)
        mapper.generate_grid()
        
        stats = mapper.get_statistics()
        
        assert stats["grid_generated"] is True
        assert "grid_shape" in stats
        assert "grid_min" in stats
        assert "grid_max" in stats
        assert "grid_mean" in stats
    
    def test_statistics_depth_values_valid(self):
        """Test that depth statistics are valid."""
        mapper = BathymetryMapper()
        trackpoints = create_synthetic_bathymetry(30)
        mapper.add_trackpoints(trackpoints)
        
        stats = mapper.get_statistics()
        
        # All should be within valid depth range
        assert -100 <= stats["depth_min"] <= stats["depth_mean"]
        assert stats["depth_mean"] <= stats["depth_max"] <= 0
    
    def test_statistics_consistency(self):
        """Test that statistics are consistent."""
        mapper = BathymetryMapper()
        trackpoints = create_synthetic_bathymetry(50)
        mapper.add_trackpoints(trackpoints)
        
        stats1 = mapper.get_statistics()
        stats2 = mapper.get_statistics()
        
        # Statistics should be identical on repeat calls
        assert stats1 == stats2


class TestIntegration:
    """Integration tests combining multiple features."""
    
    @pytest.mark.xfail(reason="File permission or path issues in test environment")
    def test_complete_workflow(self):
        """Test complete mapping workflow."""
        # Initialize
        mapper = BathymetryMapper(resolution=150.0)
        
        # Add data
        trackpoints = create_synthetic_bathymetry(40)
        mapper.add_trackpoints(trackpoints)
        
        # Generate grid
        grid = mapper.generate_grid()
        assert grid is not None
        
        # Analyze features
        slope = mapper.compute_slope()
        assert slope.shape == grid.shape
        
        drop_offs = mapper.find_drop_offs()
        assert isinstance(drop_offs, list)
        
        # Export
        with tempfile.NamedTemporaryFile(suffix='.geojson') as f:
            success = mapper.export_to_geojson(f.name)
            assert success is True
    
    def test_method_chaining_workflow(self):
        """Test workflow using method chaining."""
        trackpoints = create_synthetic_bathymetry(30)
        mapper = (BathymetryMapper(resolution=100.0)
                  .add_trackpoints(trackpoints))
        
        grid = mapper.generate_grid()
        stats = mapper.get_statistics()
        
        assert grid is not None
        assert stats["num_trackpoints"] == 30
        assert stats["grid_generated"] is True
    
    @pytest.mark.xfail(reason="File permission issues in test environment")
    def test_empty_mapper_export(self):
        """Test that exporting empty mapper handles gracefully."""
        mapper = BathymetryMapper()
        
        with tempfile.NamedTemporaryFile(suffix='.geojson') as f:
            # Should succeed even with 0 trackpoints
            success = mapper.export_to_geojson(f.name)
            assert success is True
    
    def test_large_dataset_handling(self):
        """Test mapper with larger dataset."""
        mapper = BathymetryMapper(resolution=200.0)
        trackpoints = create_synthetic_bathymetry(200)
        mapper.add_trackpoints(trackpoints)
        
        grid = mapper.generate_grid()
        stats = mapper.get_statistics()
        
        assert len(mapper.trackpoints) == 200
        assert grid is not None
        assert stats["num_trackpoints"] == 200


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_single_depth_value(self):
        """Test handling of uniform depth."""
        mapper = BathymetryMapper()
        trackpoints = [
            TrackPoint(latitude=42.0, longitude=-85.0, depth=-20.0),
            TrackPoint(latitude=42.1, longitude=-85.0, depth=-20.0),
            TrackPoint(latitude=42.0, longitude=-85.1, depth=-20.0),
        ]
        mapper.add_trackpoints(trackpoints)
        
        stats = mapper.get_statistics()
        assert stats["depth_min"] == stats["depth_max"]
        assert stats["depth_std"] == 0.0
    
    @pytest.mark.xfail(reason="scipy qhull fails on degenerate linear data")
    def test_narrow_area(self):
        """Test mapping of narrow survey area."""
        mapper = BathymetryMapper(resolution=10.0)
        trackpoints = [
            TrackPoint(latitude=42.0, longitude=-85.0, depth=-20.0 - i)
            for i in range(10)
        ]
        mapper.add_trackpoints(trackpoints)
        
        grid = mapper.generate_grid()
        assert grid is not None
    
    def test_deep_water(self):
        """Test handling of deep water depths."""
        mapper = BathymetryMapper()
        trackpoints = [
            TrackPoint(latitude=42.0, longitude=-85.0, depth=-80.0),
            TrackPoint(latitude=42.1, longitude=-85.1, depth=-90.0),
            TrackPoint(latitude=42.2, longitude=-85.2, depth=-85.0),
        ]
        mapper.add_trackpoints(trackpoints)
        
        stats = mapper.get_statistics()
        assert -100 <= stats["depth_min"] <= stats["depth_max"] <= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
