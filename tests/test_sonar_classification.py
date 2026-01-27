"""
Tests for Phase 13.1: Real-Time Sonar Signal Classification

Tests for signal feature extraction and ML-based classification.

Author: CESARops Development
Date: January 27, 2026
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import time

from src.cesarops.sonar_classification import (
    SignalType, SonarSignalFeatures, SonarSignalFeatureExtractor,
    RandomForestSignalClassifier, SonarSignalClassifier, ClassificationResult
)


# ============================================================================
# Feature Extraction Tests
# ============================================================================

class TestSonarSignalFeatureExtractor:
    """Test sonar signal feature extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create feature extractor."""
        return SonarSignalFeatureExtractor(sample_rate=44100.0)
    
    def test_extractor_creation(self, extractor):
        """Test creating feature extractor."""
        assert extractor is not None
        assert extractor.sample_rate == 44100.0
    
    def test_time_domain_features(self, extractor):
        """Test time-domain feature extraction."""
        # Create simple signal: 1 second of sine wave
        t = np.linspace(0, 1, 44100)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        features = extractor.extract_time_domain_features(signal)
        
        assert "mean" in features
        assert "std" in features
        assert "rms" in features
        assert "zero_crossing_rate" in features
        assert "energy" in features
        assert "peak_value" in features
        assert "crest_factor" in features
        
        # Verify RMS is positive
        assert features["rms"] > 0
    
    def test_frequency_domain_features(self, extractor):
        """Test frequency-domain feature extraction."""
        # Create 1kHz sine wave
        t = np.linspace(0, 1, 44100)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        features = extractor.extract_frequency_domain_features(signal)
        
        assert "dominant_frequency" in features
        assert "spectral_centroid" in features
        assert "spectral_bandwidth" in features
        assert "frequency_variance" in features
        
        # Dominant frequency should be near 1kHz
        assert 900 < features["dominant_frequency"] < 1100
    
    def test_wavelet_features(self, extractor):
        """Test wavelet feature extraction."""
        t = np.linspace(0, 1, 44100)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        features = extractor.extract_wavelet_features(signal)
        
        assert "wavelet_energy_approx" in features
        assert "wavelet_energy_detail" in features
        assert "wavelet_ratio" in features
    
    def test_extract_all_features(self, extractor):
        """Test extracting all features."""
        t = np.linspace(0, 1, 44100)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        features = extractor.extract_all_features(signal)
        
        assert isinstance(features, SonarSignalFeatures)
        assert features.mean is not None
        assert features.dominant_frequency > 0
        assert features.entropy >= 0
    
    def test_feature_vector_conversion(self, extractor):
        """Test converting features to vector."""
        t = np.linspace(0, 1, 44100)
        signal = np.sin(2 * np.pi * 1000 * t)
        features = extractor.extract_all_features(signal)
        
        vector = features.to_vector()
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 12
        assert np.isfinite(vector).all()
    
    def test_noise_signal(self, extractor):
        """Test feature extraction from noise."""
        np.random.seed(42)
        signal = np.random.randn(44100)
        
        features = extractor.extract_all_features(signal)
        
        # Noise should have high entropy
        assert features.entropy > 5
        # Noise has broad spectrum, check that dominant frequency exists
        assert features.dominant_frequency > 0
        assert features.spectral_bandwidth > 1000  # Broad spectrum for noise
    
    def test_silent_signal(self, extractor):
        """Test feature extraction from silent signal."""
        signal = np.zeros(44100)
        
        features = extractor.extract_all_features(signal)
        
        # Silent signal should have zero/near-zero features
        assert features.rms < 0.001
        assert features.energy < 0.001


# ============================================================================
# Signal Type Tests
# ============================================================================

class TestSignalTypes:
    """Test signal type enumeration."""
    
    def test_signal_types(self):
        """Test all signal types are defined."""
        types = [st.value for st in SignalType]
        assert "fish" in types
        assert "geological" in types
        assert "marine_life" in types
        assert "artifact" in types
        assert "noise" in types
        assert "unknown" in types


# ============================================================================
# Feature Data Class Tests
# ============================================================================

class TestSonarSignalFeatures:
    """Test signal features data class."""
    
    def test_features_creation(self):
        """Test creating features object."""
        features = SonarSignalFeatures(
            mean=0.5,
            std=0.1,
            rms=0.2
        )
        assert features.mean == 0.5
        assert features.std == 0.1
        assert features.rms == 0.2
    
    def test_features_vector(self):
        """Test converting features to vector."""
        features = SonarSignalFeatures(
            mean=1.0, std=2.0, rms=3.0,
            zero_crossing_rate=0.5, energy=100.0,
            peak_value=5.0, dominant_frequency=1000.0,
            spectral_centroid=800.0, spectral_bandwidth=500.0,
            frequency_variance=1000.0, crest_factor=10.0,
            entropy=5.0
        )
        
        vector = features.to_vector()
        assert len(vector) == 12
        assert vector[0] == 1.0  # mean


# ============================================================================
# Random Forest Classifier Tests
# ============================================================================

class TestRandomForestSignalClassifier:
    """Test Random Forest classifier."""
    
    @pytest.fixture
    def extractor(self):
        """Create feature extractor."""
        return SonarSignalFeatureExtractor()
    
    @pytest.fixture
    def classifier(self, extractor):
        """Create classifier."""
        return RandomForestSignalClassifier(extractor)
    
    def test_classifier_creation(self, classifier):
        """Test creating classifier."""
        assert classifier is not None
        assert classifier.model is not None
    
    def test_model_info(self, classifier):
        """Test getting model information."""
        info = classifier.get_model_info()
        assert "model_type" in info
        assert info["model_type"] == "RandomForest"
        assert "accuracy" in info
    
    def test_untrained_classification(self, classifier):
        """Test classification with untrained model."""
        features = SonarSignalFeatures(mean=1.0, std=0.5, rms=0.7)
        
        signal_type, confidence = classifier.classify(features)
        
        assert signal_type == SignalType.UNKNOWN
        assert confidence == 0.5
    
    def test_batch_classification(self, classifier):
        """Test batch classification."""
        features_list = [
            SonarSignalFeatures(mean=1.0, std=0.5, rms=0.7),
            SonarSignalFeatures(mean=2.0, std=0.6, rms=0.8),
        ]
        
        results = classifier.batch_classify(features_list)
        
        assert len(results) == 2
        assert all(isinstance(r, tuple) for r in results)


# ============================================================================
# High-Level Classifier Tests
# ============================================================================

class TestSonarSignalClassifier:
    """Test high-level signal classifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create signal classifier."""
        return SonarSignalClassifier(model_type="random_forest")
    
    def test_classifier_creation(self, classifier):
        """Test creating classifier."""
        assert classifier is not None
        assert classifier.feature_extractor is not None
        assert classifier.classifier is not None
    
    def test_sine_wave_classification(self, classifier):
        """Test classifying sine wave signal."""
        # Create 1kHz sine wave
        t = np.linspace(0, 0.1, 4410)  # 100ms at 44.1kHz
        signal = np.sin(2 * np.pi * 1000 * t)
        
        result = classifier.classify(signal)
        
        assert isinstance(result, ClassificationResult)
        assert result.signal_type in SignalType
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time_ms > 0
    
    def test_classification_with_id(self, classifier):
        """Test classification with signal ID."""
        t = np.linspace(0, 0.1, 4410)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        result = classifier.classify(signal, signal_id="test_signal_1")
        
        assert result.signal_id == "test_signal_1"
    
    def test_batch_classification(self, classifier):
        """Test batch classification."""
        t = np.linspace(0, 0.1, 4410)
        signals = [
            np.sin(2 * np.pi * 1000 * t),
            np.cos(2 * np.pi * 1000 * t),
            np.random.randn(4410) * 0.1
        ]
        
        results = classifier.batch_classify(signals)
        
        assert len(results) == 3
        assert all(isinstance(r, ClassificationResult) for r in results)
    
    def test_processing_latency(self, classifier):
        """Test classification latency is acceptable."""
        t = np.linspace(0, 0.1, 4410)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        result = classifier.classify(signal)
        
        # Should process in <100ms
        assert result.processing_time_ms < 100
    
    def test_classification_history(self, classifier):
        """Test classification history tracking."""
        t = np.linspace(0, 0.1, 4410)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        # Classify multiple signals
        for i in range(5):
            classifier.classify(signal, signal_id=f"sig_{i}")
        
        history = classifier.get_classification_history()
        assert len(history) == 5
    
    def test_statistics(self, classifier):
        """Test classification statistics."""
        t = np.linspace(0, 0.1, 4410)
        signal = np.sin(2 * np.pi * 1000 * t)
        
        # Classify multiple signals
        for i in range(3):
            classifier.classify(signal)
        
        stats = classifier.get_statistics()
        
        assert "total_classifications" in stats
        assert stats["total_classifications"] == 3
        assert "type_counts" in stats
        assert "average_confidence" in stats
    
    def test_model_info(self, classifier):
        """Test getting model information."""
        info = classifier.get_model_info()
        
        assert "model_type" in info
        assert "feature_count" in info
        assert "signal_types" in info
        assert len(info["signal_types"]) > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestClassificationIntegration:
    """Test end-to-end classification integration."""
    
    def test_signal_to_classification_pipeline(self):
        """Test complete pipeline from signal to classification."""
        classifier = SonarSignalClassifier()
        
        # Create different types of signals
        t = np.linspace(0, 0.1, 4410)
        
        # Fish-like signal (complex waveform)
        fish_signal = (
            np.sin(2 * np.pi * 500 * t) + 
            0.5 * np.sin(2 * np.pi * 1000 * t) +
            0.3 * np.sin(2 * np.pi * 2000 * t)
        )
        
        # Noise
        noise_signal = np.random.randn(4410) * 0.1
        
        # Classify
        fish_result = classifier.classify(fish_signal, "fish_test")
        noise_result = classifier.classify(noise_signal, "noise_test")
        
        assert fish_result.signal_type in SignalType
        assert noise_result.signal_type in SignalType
        
        # Verify results are tracked
        history = classifier.get_classification_history()
        assert len(history) >= 2
    
    def test_large_batch_classification(self):
        """Test classification of large signal batch."""
        classifier = SonarSignalClassifier()
        
        # Create 100 random signals
        signals = [
            np.random.randn(4410) * 0.1
            for _ in range(100)
        ]
        
        results = classifier.batch_classify(signals)
        
        assert len(results) == 100
        assert all(r.processing_time_ms < 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
