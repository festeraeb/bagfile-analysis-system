"""
Comprehensive test suite for Phase 13.2: Multi-Sensor Fusion

Tests cover:
- 35+ tests validating all fusion components
- Sensor registration and data bus operations
- Quality estimation across all sensor types
- Coordinate system transformations
- Multi-sensor fusion and correlation
- Environmental context generation
- Latency and synchronization
"""

import pytest
import numpy as np
from datetime import datetime
from typing import List
import sys
from pathlib import Path

# Add src to path to import cesarops modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cesarops.sensor_fusion import (
    BaseSensor, SensorType, CoordinateSystem, Location,
    SensorReading, SensorReadings, SensorDataBus,
    SensorQualityEstimator, CoordinateSystemManager,
    FusedData, CorrelationResult, EnvironmentalContext,
    FusionEngine
)


# ============================================================================
# Mock Sensor Implementations
# ============================================================================

class MockSonarSensor(BaseSensor):
    """Mock sonar sensor for testing."""
    
    def __init__(self, intensity_value: float = 0.7):
        super().__init__(SensorType.SONAR, "MockSonar")
        self.intensity_value = intensity_value
        self.available = True
    
    def read(self) -> SensorReading:
        self.read_count += 1
        self.last_reading = SensorReading(
            sensor_type=SensorType.SONAR,
            value=self.intensity_value,
            location=Location(-87.0, 42.5, 50.0),
            quality=0.9,
            confidence=0.85,
            units="dB"
        )
        return self.last_reading
    
    def is_available(self) -> bool:
        return self.available


class MockBathymetrySensor(BaseSensor):
    """Mock bathymetry sensor for testing."""
    
    def __init__(self, depth_value: float = 100.0):
        super().__init__(SensorType.BATHYMETRY, "MockBathy")
        self.depth_value = depth_value
        self.available = True
    
    def read(self) -> SensorReading:
        self.read_count += 1
        self.last_reading = SensorReading(
            sensor_type=SensorType.BATHYMETRY,
            value={"depth": self.depth_value, "slope": 2.5},
            location=Location(-87.0, 42.5, self.depth_value),
            quality=0.95,
            confidence=0.92,
            units="meters"
        )
        return self.last_reading
    
    def is_available(self) -> bool:
        return self.available


class MockCurrentSensor(BaseSensor):
    """Mock current sensor for testing."""
    
    def __init__(self, u: float = 0.1, v: float = 0.05):
        super().__init__(SensorType.CURRENT, "MockCurrent")
        self.u = u
        self.v = v
        self.available = True
    
    def read(self) -> SensorReading:
        self.read_count += 1
        self.last_reading = SensorReading(
            sensor_type=SensorType.CURRENT,
            value=[self.u, self.v],
            location=Location(-87.0, 42.5, 25.0),
            quality=0.85,
            confidence=0.80,
            units="m/s"
        )
        return self.last_reading
    
    def is_available(self) -> bool:
        return self.available


class MockTemperatureSensor(BaseSensor):
    """Mock temperature sensor for testing."""
    
    def __init__(self, temp_value: float = 15.5):
        super().__init__(SensorType.TEMPERATURE, "MockTemp")
        self.temp_value = temp_value
        self.available = True
    
    def read(self) -> SensorReading:
        self.read_count += 1
        self.last_reading = SensorReading(
            sensor_type=SensorType.TEMPERATURE,
            value=self.temp_value,
            quality=0.88,
            confidence=0.85,
            units="Celsius"
        )
        return self.last_reading
    
    def is_available(self) -> bool:
        return self.available


# ============================================================================
# Test: Sensor Data Bus
# ============================================================================

class TestSensorDataBus:
    """Test sensor registration and data bus operations."""
    
    def test_register_sensor(self):
        """Test sensor registration."""
        bus = SensorDataBus()
        sonar = MockSonarSensor()
        
        bus.register_sensor(sonar)
        assert bus.get_sensor(SensorType.SONAR) is sonar
    
    def test_register_multiple_sensors(self):
        """Test registering multiple sensors."""
        bus = SensorDataBus()
        sonar = MockSonarSensor()
        bathy = MockBathymetrySensor()
        current = MockCurrentSensor()
        
        bus.register_sensor(sonar)
        bus.register_sensor(bathy)
        bus.register_sensor(current)
        
        assert len(bus.sensors) == 3
        assert bus.get_sensor(SensorType.SONAR) is sonar
        assert bus.get_sensor(SensorType.BATHYMETRY) is bathy
        assert bus.get_sensor(SensorType.CURRENT) is current
    
    def test_unregister_sensor(self):
        """Test sensor unregistration."""
        bus = SensorDataBus()
        sonar = MockSonarSensor()
        
        bus.register_sensor(sonar)
        assert bus.get_sensor(SensorType.SONAR) is sonar
        
        bus.unregister_sensor(SensorType.SONAR)
        assert bus.get_sensor(SensorType.SONAR) is None
    
    def test_poll_all_sensors(self):
        """Test polling all sensors."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor())
        bus.register_sensor(MockCurrentSensor())
        
        readings = bus.poll_all_sensors()
        
        assert readings.has_reading(SensorType.SONAR)
        assert readings.has_reading(SensorType.BATHYMETRY)
        assert readings.has_reading(SensorType.CURRENT)
        assert len(readings.readings) == 3
    
    def test_poll_partial_sensors(self):
        """Test polling with only some sensors available."""
        bus = SensorDataBus()
        sonar = MockSonarSensor()
        sonar.available = False
        
        bus.register_sensor(sonar)
        bus.register_sensor(MockBathymetrySensor())
        
        readings = bus.poll_all_sensors()
        
        assert not readings.has_reading(SensorType.SONAR)
        assert readings.has_reading(SensorType.BATHYMETRY)
    
    def test_get_data_quality(self):
        """Test data quality metrics."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor())
        
        bus.poll_all_sensors()
        quality = bus.get_data_quality()
        
        assert "sonar" in quality
        assert "bathymetry" in quality
        assert 0.0 <= quality["sonar"] <= 1.0
        assert 0.0 <= quality["bathymetry"] <= 1.0
    
    def test_get_available_sensors(self):
        """Test getting list of available sensors."""
        bus = SensorDataBus()
        sonar = MockSonarSensor()
        bathy = MockBathymetrySensor()
        bathy.available = False
        
        bus.register_sensor(sonar)
        bus.register_sensor(bathy)
        
        available = bus.get_available_sensors()
        assert SensorType.SONAR in available
        assert SensorType.BATHYMETRY not in available


# ============================================================================
# Test: Sensor Quality Estimation
# ============================================================================

class TestSensorQualityEstimator:
    """Test quality estimation for all sensor types."""
    
    def test_estimate_sonar_quality(self):
        """Test sonar quality estimation."""
        estimator = SensorQualityEstimator()
        
        quality = estimator.estimate_sonar_quality(
            signal_strength=0.9,
            noise_level=0.05,
            multipath_error=0.02
        )
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.8  # Should be high with good params
    
    def test_estimate_bathymetry_quality(self):
        """Test bathymetry quality estimation."""
        estimator = SensorQualityEstimator()
        
        quality = estimator.estimate_bathymetry_quality(
            coverage=0.95,
            resolution=0.8,
            age_hours=12
        )
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.7  # Should be decent
    
    def test_estimate_current_quality(self):
        """Test current quality estimation."""
        estimator = SensorQualityEstimator()
        
        quality = estimator.estimate_current_quality(
            station_proximity_km=5.0,
            data_freshness_minutes=15
        )
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.6  # Should be good
    
    def test_estimate_temperature_quality(self):
        """Test temperature quality estimation."""
        estimator = SensorQualityEstimator()
        
        quality = estimator.estimate_temperature_quality(
            measurement_error=0.2,
            calibration_days_ago=15
        )
        
        assert 0.0 <= quality <= 1.0
    
    def test_quality_history_tracking(self):
        """Test quality history tracking."""
        estimator = SensorQualityEstimator()
        
        for i in range(5):
            estimator.estimate_sonar_quality(
                signal_strength=0.8 + (i * 0.02)
            )
        
        avg_quality = estimator.get_average_quality(SensorType.SONAR)
        assert 0.0 <= avg_quality <= 1.0
        assert len(estimator.quality_history[SensorType.SONAR]) == 5
    
    def test_poor_sonar_quality(self):
        """Test sonar quality with poor conditions."""
        estimator = SensorQualityEstimator()
        
        quality = estimator.estimate_sonar_quality(
            signal_strength=0.2,
            noise_level=0.9,
            multipath_error=0.8
        )
        
        assert quality < 0.5  # Should be low


# ============================================================================
# Test: Coordinate System Management
# ============================================================================

class TestCoordinateSystemManager:
    """Test coordinate system transformations."""
    
    def test_system_registration(self):
        """Test registering new coordinate systems."""
        manager = CoordinateSystemManager()
        
        manager.register_coordinate_system("custom", {
            "origin": (10.0, 20.0),
            "units": "meters"
        })
        
        info = manager.get_system_info(CoordinateSystem.WGS84)
        assert info is not None
    
    def test_wgs84_to_local_transform(self):
        """Test WGS84 to Great Lakes Local transformation."""
        manager = CoordinateSystemManager()
        
        # WGS84 point
        point = Location(42.5, -87.0, 50.0, CoordinateSystem.WGS84)
        
        # Transform to Great Lakes Local
        transformed = manager.transform(point, CoordinateSystem.GREAT_LAKES_LOCAL)
        
        assert transformed.coordinate_system == CoordinateSystem.GREAT_LAKES_LOCAL
        assert transformed.z == 50.0  # Z unchanged
    
    def test_local_to_wgs84_transform(self):
        """Test Great Lakes Local to WGS84 transformation."""
        manager = CoordinateSystemManager()
        
        # Local point (5km north, 10km east of origin)
        point = Location(5.0, 10.0, 50.0, CoordinateSystem.GREAT_LAKES_LOCAL)
        
        # Transform to WGS84
        transformed = manager.transform(point, CoordinateSystem.WGS84)
        
        assert transformed.coordinate_system == CoordinateSystem.WGS84
    
    def test_same_system_transform(self):
        """Test transforming to same coordinate system."""
        manager = CoordinateSystemManager()
        
        point = Location(42.5, -87.0, 50.0, CoordinateSystem.WGS84)
        transformed = manager.transform(point, CoordinateSystem.WGS84)
        
        assert point is transformed  # Should return same object


# ============================================================================
# Test: Fusion Engine
# ============================================================================

class TestFusionEngine:
    """Test multi-sensor fusion operations."""
    
    def test_fusion_engine_initialization(self):
        """Test initializing fusion engine."""
        bus = SensorDataBus()
        engine = FusionEngine(bus)
        
        assert engine.sensor_bus is bus
        assert engine.coordinate_system == CoordinateSystem.WGS84
    
    def test_fuse_single_sensor(self):
        """Test fusing data from single sensor."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        engine = FusionEngine(bus)
        
        fused = engine.fuse_readings()
        
        assert fused.sonar_intensity is not None
        assert SensorType.SONAR in fused.contributing_sensors
        assert fused.fusion_confidence > 0.0
    
    def test_fuse_multiple_sensors(self):
        """Test fusing data from multiple sensors."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor())
        bus.register_sensor(MockCurrentSensor())
        bus.register_sensor(MockTemperatureSensor())
        
        engine = FusionEngine(bus)
        fused = engine.fuse_readings()
        
        assert fused.sonar_intensity is not None
        assert fused.depth is not None
        assert fused.current_velocity is not None
        assert fused.temperature is not None
        assert len(fused.contributing_sensors) == 4
    
    def test_fusion_confidence(self):
        """Test fusion confidence calculation."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor())
        
        engine = FusionEngine(bus)
        fused = engine.fuse_readings()
        
        assert 0.0 <= fused.fusion_confidence <= 1.0
        assert fused.fusion_confidence > 0.5  # Should be decent with good sensors
    
    def test_correlate_anomalies(self):
        """Test anomaly correlation across sensors."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor(depth_value=50.0))
        bus.register_sensor(MockCurrentSensor(u=0.2, v=0.15))
        
        engine = FusionEngine(bus)
        
        location = Location(-87.0, 42.5, 25.0)
        correlation = engine.correlate_anomalies("anomaly_001", location)
        
        assert correlation.primary_anomaly_id == "anomaly_001"
        assert correlation.correlation_score >= 0.0
        assert len(correlation.environmental_conditions) > 0
    
    def test_environmental_context(self):
        """Test environmental context generation."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor(depth_value=75.0))
        bus.register_sensor(MockCurrentSensor(u=0.15, v=0.1))
        bus.register_sensor(MockTemperatureSensor(temp_value=18.5))
        
        engine = FusionEngine(bus)
        location = Location(-87.0, 42.5, 0.0)
        
        context = engine.get_environmental_context(location)
        
        assert context.depth > 0
        assert context.temperature > 0
        assert context.current_strength >= 0.0
        assert context.overall_quality > 0.0
        assert context.sensor_count == 4
    
    def test_fusion_history(self):
        """Test fusion history tracking."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        engine = FusionEngine(bus)
        
        # Multiple fusions
        for _ in range(5):
            engine.fuse_readings()
        
        history = engine.get_fusion_history(limit=3)
        assert len(history) == 3
    
    def test_synchronization_quality(self):
        """Test synchronization quality calculation."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor())
        
        engine = FusionEngine(bus)
        fused = engine.fuse_readings()
        
        assert fused.synchronization_quality <= 1.0


# ============================================================================
# Test: Data Classes and Structures
# ============================================================================

class TestLocationDataClass:
    """Test Location data class."""
    
    def test_location_creation(self):
        """Test creating location."""
        loc = Location(-87.0, 42.5, 50.0)
        
        assert loc.x == -87.0
        assert loc.y == 42.5
        assert loc.z == 50.0
        assert loc.coordinate_system == CoordinateSystem.WGS84
    
    def test_location_with_uncertainty(self):
        """Test location with uncertainty."""
        loc = Location(-87.0, 42.5, 50.0, uncertainty=2.5)
        
        assert loc.uncertainty == 2.5
    
    def test_location_hashable(self):
        """Test location is hashable for use in sets/dicts."""
        loc1 = Location(-87.0, 42.5, 50.0)
        loc2 = Location(-87.0, 42.5, 50.0)
        
        location_set = {loc1, loc2}
        assert len(location_set) == 1


class TestSensorReadingDataClass:
    """Test SensorReading data class."""
    
    def test_sensor_reading_creation(self):
        """Test creating sensor reading."""
        reading = SensorReading(
            sensor_type=SensorType.SONAR,
            value=0.75,
            quality=0.9,
            units="dB"
        )
        
        assert reading.sensor_type == SensorType.SONAR
        assert reading.value == 0.75
        assert reading.quality == 0.9
        assert reading.timestamp > 0


class TestFusedDataDataClass:
    """Test FusedData data class."""
    
    def test_fused_data_creation(self):
        """Test creating fused data."""
        fused = FusedData(
            timestamp=datetime.now().timestamp(),
            location=Location(-87.0, 42.5, 0.0),
            sonar_intensity=0.85,
            depth=100.0
        )
        
        assert fused.sonar_intensity == 0.85
        assert fused.depth == 100.0
        assert len(fused.contributing_sensors) == 0


class TestCorrelationResultDataClass:
    """Test CorrelationResult data class."""
    
    def test_correlation_result_creation(self):
        """Test creating correlation result."""
        result = CorrelationResult(
            primary_anomaly_id="test_anomaly",
            timestamp=datetime.now().timestamp(),
            correlation_score=0.75,
            likely_cause="geological_feature"
        )
        
        assert result.primary_anomaly_id == "test_anomaly"
        assert result.correlation_score == 0.75
        assert result.likely_cause == "geological_feature"


class TestEnvironmentalContextDataClass:
    """Test EnvironmentalContext data class."""
    
    def test_environmental_context_creation(self):
        """Test creating environmental context."""
        context = EnvironmentalContext(
            location=Location(-87.0, 42.5, 0.0),
            timestamp=datetime.now().timestamp(),
            depth=75.0,
            temperature=16.5,
            current_strength=0.2
        )
        
        assert context.depth == 75.0
        assert context.temperature == 16.5
        assert context.current_strength == 0.2


# ============================================================================
# Test: Integration Scenarios
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_fusion_workflow(self):
        """Test complete fusion workflow."""
        # Setup sensor bus
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor(intensity_value=0.8))
        bus.register_sensor(MockBathymetrySensor(depth_value=60.0))
        bus.register_sensor(MockCurrentSensor(u=0.12, v=0.08))
        bus.register_sensor(MockTemperatureSensor(temp_value=17.2))
        
        # Create fusion engine
        engine = FusionEngine(bus)
        
        # Get fused data
        fused = engine.fuse_readings()
        
        # Verify all data was integrated
        assert fused.sonar_intensity == 0.8
        assert fused.depth == 60.0
        assert fused.temperature == 17.2
        assert len(fused.contributing_sensors) == 4
        assert fused.fusion_confidence > 0.8
    
    def test_anomaly_correlation_workflow(self):
        """Test anomaly correlation workflow."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor())
        bus.register_sensor(MockCurrentSensor())
        
        engine = FusionEngine(bus)
        
        # Correlate anomaly
        location = Location(-87.0, 42.5, 30.0)
        correlation = engine.correlate_anomalies("anomaly_test", location)
        
        assert correlation.primary_anomaly_id == "anomaly_test"
        assert len(correlation.environmental_conditions) > 0
        assert correlation.correlation_score >= 0.0
    
    def test_context_generation_workflow(self):
        """Test environmental context generation workflow."""
        bus = SensorDataBus()
        bus.register_sensor(MockSonarSensor())
        bus.register_sensor(MockBathymetrySensor(depth_value=80.0))
        bus.register_sensor(MockCurrentSensor(u=0.1, v=0.05))
        bus.register_sensor(MockTemperatureSensor(temp_value=15.0))
        
        engine = FusionEngine(bus)
        location = Location(-87.0, 42.5, 0.0)
        
        context = engine.get_environmental_context(location)
        
        assert context.depth == 80.0
        assert context.temperature == 15.0
        assert context.sensor_count == 4
        assert context.overall_quality > 0.5


# ============================================================================
# Test: Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_sensor_bus(self):
        """Test with no sensors registered."""
        bus = SensorDataBus()
        engine = FusionEngine(bus)
        
        fused = engine.fuse_readings()
        
        assert len(fused.contributing_sensors) == 0
        assert fused.fusion_confidence == 0.0
    
    def test_partial_sensor_failure(self):
        """Test with some sensors unavailable."""
        bus = SensorDataBus()
        sonar = MockSonarSensor()
        sonar.available = False
        
        bus.register_sensor(sonar)
        bus.register_sensor(MockBathymetrySensor())
        
        engine = FusionEngine(bus)
        fused = engine.fuse_readings()
        
        assert SensorType.SONAR not in fused.contributing_sensors
        assert SensorType.BATHYMETRY in fused.contributing_sensors
    
    def test_coordinate_transform_with_depth(self):
        """Test coordinate transformation preserves depth."""
        manager = CoordinateSystemManager()
        
        point = Location(42.5, -87.0, 150.0, CoordinateSystem.WGS84)
        transformed = manager.transform(point, CoordinateSystem.GREAT_LAKES_LOCAL)
        
        assert transformed.z == 150.0
    
    def test_quality_estimation_bounds(self):
        """Test quality stays within bounds."""
        estimator = SensorQualityEstimator()
        
        # Test with extreme values
        quality1 = estimator.estimate_sonar_quality(
            signal_strength=0.0,
            noise_level=1.0,
            multipath_error=1.0
        )
        assert 0.0 <= quality1 <= 1.0
        
        quality2 = estimator.estimate_sonar_quality(
            signal_strength=1.0,
            noise_level=0.0,
            multipath_error=0.0
        )
        assert 0.0 <= quality2 <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
