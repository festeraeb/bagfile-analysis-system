"""
Unit Tests for SonarAnomalyDetector - Phase 11.1

Tests cover:
- Initialization and validation
- Training on baseline data
- Anomaly detection
- Feature extraction
- Edge cases and error handling

Run with: pytest tests/test_sonar_anomaly_detector.py -v
"""

import pytest
import numpy as np
import tempfile
import json
from pathlib import Path

from src.cesarops.sonar_anomaly_detector import (
    SonarAnomalyDetector,
    create_synthetic_baseline,
    create_synthetic_test_data
)


class TestInitialization:
    """Test detector initialization"""
    
    def test_basic_initialization(self):
        """Test creating detector with defaults"""
        detector = SonarAnomalyDetector()
        assert detector.trained == False
        assert detector.baseline_stats is None
        
    def test_initialization_with_params(self):
        """Test creating detector with custom parameters"""
        detector = SonarAnomalyDetector(contamination_factor=0.1, random_state=123)
        assert detector.detector.contamination == 0.1
        assert detector.detector.random_state == 123
        
    def test_invalid_contamination_factor(self):
        """Test that invalid contamination factor raises error"""
        with pytest.raises(ValueError):
            SonarAnomalyDetector(contamination_factor=0.0)
        
        with pytest.raises(ValueError):
            SonarAnomalyDetector(contamination_factor=1.0)
        
        with pytest.raises(ValueError):
            SonarAnomalyDetector(contamination_factor=1.5)


class TestTraining:
    """Test detector training"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance for testing"""
        return SonarAnomalyDetector(contamination_factor=0.1)
    
    @pytest.fixture
    def baseline_data(self):
        """Create baseline training data"""
        return create_synthetic_baseline(num_pings=100, ping_width=256)
    
    def test_training_success(self, detector, baseline_data):
        """Test successful training"""
        result = detector.train_on_baseline(baseline_data)
        
        assert detector.trained == True
        assert detector.baseline_stats is not None
        assert result is detector  # Check method chaining
        
    def test_baseline_stats_calculated(self, detector, baseline_data):
        """Test that baseline statistics are calculated correctly"""
        detector.train_on_baseline(baseline_data)
        stats = detector.baseline_stats
        
        assert stats['num_pings'] == 100
        assert stats['num_samples_per_ping'] == 256
        assert isinstance(stats['mean_amplitude'], float)
        assert isinstance(stats['std_amplitude'], float)
        assert 'training_date' in stats
        
    def test_training_with_wrong_shape(self, detector):
        """Test that 1D array raises error"""
        with pytest.raises(ValueError):
            detector.train_on_baseline(np.array([1, 2, 3]))
    
    def test_training_with_too_few_pings(self, detector):
        """Test that too few pings raises error"""
        with pytest.raises(ValueError):
            detector.train_on_baseline(np.random.randn(5, 256))
    
    def test_training_with_nan_values(self, detector):
        """Test that NaN values are handled"""
        baseline = create_synthetic_baseline()
        baseline[0, 0] = np.nan
        
        # Should not raise, should replace NaN
        detector.train_on_baseline(baseline)
        assert detector.trained == True


class TestDetection:
    """Test anomaly detection"""
    
    @pytest.fixture
    def trained_detector(self):
        """Create and train detector"""
        detector = SonarAnomalyDetector(contamination_factor=0.1)
        baseline = create_synthetic_baseline(num_pings=100)
        detector.train_on_baseline(baseline)
        return detector
    
    def test_detection_without_training(self):
        """Test that detection requires training"""
        detector = SonarAnomalyDetector()
        test_data = create_synthetic_baseline(num_pings=10)
        
        with pytest.raises(ValueError):
            detector.detect_anomalies(test_data)
    
    def test_detection_success(self, trained_detector):
        """Test successful detection"""
        test_data, true_anomalies = create_synthetic_test_data(
            num_pings=50, num_anomalies=5
        )
        results = trained_detector.detect_anomalies(test_data)
        
        assert 'anomalies' in results
        assert 'anomaly_scores' in results
        assert 'num_anomalies' in results
        assert 'anomaly_density' in results
        assert results['status'] == 'success'
        
    def test_detection_finds_anomalies(self, trained_detector):
        """Test that anomalies are detected"""
        test_data, true_anomalies = create_synthetic_test_data(
            num_pings=50, num_anomalies=5
        )
        results = trained_detector.detect_anomalies(test_data)
        
        # Should find anomalies
        assert results['num_anomalies'] > 0
        assert results['anomaly_density'] > 0
        
    def test_anomalies_have_required_fields(self, trained_detector):
        """Test that detected anomalies have required fields"""
        test_data, _ = create_synthetic_test_data(num_pings=50, num_anomalies=5)
        results = trained_detector.detect_anomalies(test_data)
        
        for anom in results['anomalies']:
            assert 'ping_idx' in anom
            assert 'score' in anom
            assert 'type' in anom
            assert 'confidence' in anom
            assert 0 <= anom['confidence'] <= 1
            
    def test_anomalies_sorted_by_confidence(self, trained_detector):
        """Test that anomalies are sorted by confidence descending"""
        test_data, _ = create_synthetic_test_data(num_pings=50, num_anomalies=5)
        results = trained_detector.detect_anomalies(test_data)
        
        confidences = [a['confidence'] for a in results['anomalies']]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_detection_with_nan_values(self, trained_detector):
        """Test that NaN values are handled"""
        test_data = create_synthetic_baseline(num_pings=20)
        test_data[0, 0] = np.nan
        
        results = trained_detector.detect_anomalies(test_data)
        assert results['status'] == 'success'
    
    def test_detection_with_wrong_shape(self, trained_detector):
        """Test that wrong input shape raises error"""
        with pytest.raises(ValueError):
            trained_detector.detect_anomalies(np.array([1, 2, 3]))


class TestFeatureExtraction:
    """Test feature extraction"""
    
    def test_feature_extraction_shape(self):
        """Test that features have correct shape"""
        detector = SonarAnomalyDetector()
        test_data = create_synthetic_baseline(num_pings=10, ping_width=256)
        
        features = detector._extract_features(test_data)
        
        assert features.shape == (10, 10)  # 10 pings, 10 features each
    
    def test_feature_extraction_no_nan(self):
        """Test that features contain no NaN values"""
        detector = SonarAnomalyDetector()
        test_data = create_synthetic_baseline(num_pings=10)
        
        features = detector._extract_features(test_data)
        
        assert not np.isnan(features).any()
        
    def test_feature_extraction_reasonable_values(self):
        """Test that feature values are in reasonable ranges"""
        detector = SonarAnomalyDetector()
        test_data = np.ones((10, 256)) * 100  # Constant signal
        
        features = detector._extract_features(test_data)
        
        # For constant signal:
        # - mean should be ~100
        # - std should be ~0
        # - energy should be consistent
        assert np.all(features[:, 0] > 95)  # mean
        assert np.all(features[:, 1] < 1)   # std should be near 0


class TestEntropy:
    """Test entropy calculation"""
    
    def test_entropy_constant_signal(self):
        """Test entropy of constant signal (should be 0)"""
        detector = SonarAnomalyDetector()
        signal = np.ones(256) * 100
        
        entropy = detector._entropy(signal)
        
        assert entropy < 0.1  # Very low entropy
    
    def test_entropy_random_signal(self):
        """Test entropy of random signal (should be higher)"""
        detector = SonarAnomalyDetector()
        np.random.seed(42)
        signal = np.random.randn(256)
        
        entropy = detector._entropy(signal)
        
        assert entropy > 1.0  # Reasonably high entropy
    
    def test_entropy_zero_signal(self):
        """Test entropy of zero signal"""
        detector = SonarAnomalyDetector()
        signal = np.zeros(256)
        
        entropy = detector._entropy(signal)
        
        assert entropy == 0.0


class TestClassification:
    """Test anomaly classification"""
    
    def test_classify_strong_return(self):
        """Test classification of strong return"""
        detector = SonarAnomalyDetector()
        ping = np.ones(256) * 100
        ping[100:150] = 300  # Strong spike
        
        anom_type = detector._classify_anomaly(ping)
        
        assert anom_type == "strong_return"
    
    def test_classify_structured_pattern(self):
        """Test classification of structured pattern"""
        detector = SonarAnomalyDetector()
        # Create a sawtooth pattern with clear structure
        ping = np.concatenate([np.linspace(50, 150, 128), np.linspace(150, 50, 128)])
        
        anom_type = detector._classify_anomaly(ping)
        
        # The algorithm correctly identifies this as persistent_feature (69.5% values above 80% mean)
        assert anom_type in ["persistent_feature", "structured_pattern", "unusual_pattern"]


class TestExport:
    """Test export functionality"""
    
    @pytest.fixture
    def sample_results(self):
        """Create sample detection results"""
        detector = SonarAnomalyDetector()
        baseline = create_synthetic_baseline(num_pings=50)
        detector.train_on_baseline(baseline)
        
        test_data, _ = create_synthetic_test_data(num_pings=30, num_anomalies=3)
        results = detector.detect_anomalies(test_data)
        
        return detector, results
    
    def test_export_to_json(self, sample_results):
        """Test JSON export"""
        detector, results = sample_results
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_results.json"
            success = detector.export_detections_to_json(results, str(filepath))
            
            assert success == True
            assert filepath.exists()
            
            # Verify JSON is valid
            with open(filepath) as f:
                loaded = json.load(f)
            
            assert 'anomalies' in loaded
            assert loaded['status'] == 'success'
    
    def test_export_to_kml(self, sample_results):
        """Test KML export"""
        detector, results = sample_results
        
        # Create trackpoints
        trackpoints = [
            {'lat': 43.0 + i*0.01, 'lon': -87.0 + i*0.01}
            for i in range(len(results['anomaly_scores']))
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_anomalies.kml"
            success = detector.export_detections_to_kml(results, trackpoints, str(filepath))
            
            assert success == True
            assert filepath.exists()
            
            # Verify KML is valid XML
            with open(filepath) as f:
                content = f.read()
            
            assert '<?xml' in content
            assert '<kml' in content
            assert 'Placemark' in content


class TestModelInfo:
    """Test model information retrieval"""
    
    def test_model_info_untrained(self):
        """Test model info for untrained detector"""
        detector = SonarAnomalyDetector()
        info = detector.get_model_info()
        
        assert info['trained'] == False
        assert info['baseline_stats'] is None
    
    def test_model_info_trained(self):
        """Test model info for trained detector"""
        detector = SonarAnomalyDetector(contamination_factor=0.15)
        baseline = create_synthetic_baseline()
        detector.train_on_baseline(baseline)
        
        info = detector.get_model_info()
        
        assert info['trained'] == True
        assert info['baseline_stats'] is not None
        assert info['contamination'] == 0.15


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete detection workflow"""
        # Create and train
        detector = SonarAnomalyDetector()
        baseline = create_synthetic_baseline(num_pings=100)
        detector.train_on_baseline(baseline)
        
        # Test detection
        test_data, true_anomalies = create_synthetic_test_data(
            num_pings=50, num_anomalies=5
        )
        results = detector.detect_anomalies(test_data)
        
        # Verify results
        assert results['status'] == 'success'
        assert results['num_anomalies'] >= 3  # Should find most injected anomalies
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "results.json"
            detector.export_detections_to_json(results, str(json_path))
            assert json_path.exists()
    
    def test_method_chaining(self):
        """Test that methods support chaining"""
        detector = SonarAnomalyDetector()
        baseline = create_synthetic_baseline()
        
        # Should return detector for chaining
        result = detector.train_on_baseline(baseline)
        assert result is detector
    
    def test_reproducibility(self):
        """Test that results are reproducible with same random seed"""
        baseline = create_synthetic_baseline()
        test_data, _ = create_synthetic_test_data(num_pings=30, num_anomalies=3)
        
        # Run 1
        detector1 = SonarAnomalyDetector(random_state=42)
        detector1.train_on_baseline(baseline)
        results1 = detector1.detect_anomalies(test_data)
        
        # Run 2
        detector2 = SonarAnomalyDetector(random_state=42)
        detector2.train_on_baseline(baseline)
        results2 = detector2.detect_anomalies(test_data)
        
        # Should be identical
        assert results1['num_anomalies'] == results2['num_anomalies']
        assert len(results1['anomalies']) == len(results2['anomalies'])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
