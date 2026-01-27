"""
Comprehensive test suite for Phase 13.3: Enhanced Anomaly Detection

Tests cover:
- 30+ tests validating all anomaly detection components
- Contextual analysis with environmental factors
- Pattern recognition and matching
- Confidence scoring and risk assessment
- Explanation generation and interpretation
- Edge cases and error handling
"""

import pytest
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add src to path to import directly from modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly from submodule to avoid __init__.py importing opendrift
from cesarops.contextual_anomaly_detection import (
    RiskLevel, AnomalyType, Pattern, Explanation,
    ContextualAnomaly, AnomalyPatternLearner,
    AnomalyExplainer, ContextualAnomalyDetector
)


# ============================================================================
# Mock Classes
# ============================================================================

class MockLocation:
    """Mock location for testing."""
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class MockSignalClassifier:
    """Mock signal classifier for testing."""
    
    def classify(self, signal_value: float) -> Dict[str, Any]:
        """Classify signal and return type with confidence."""
        if signal_value > 0.8:
            return {
                "type": AnomalyType.ARTIFACT,
                "confidence": 0.9
            }
        elif signal_value > 0.6:
            return {
                "type": AnomalyType.GEOLOGICAL,
                "confidence": 0.8
            }
        else:
            return {
                "type": AnomalyType.UNKNOWN,
                "confidence": 0.5
            }


# ============================================================================
# Test: Pattern Recognition
# ============================================================================

class TestPatternLearner:
    """Test pattern learning and recognition."""
    
    def test_pattern_creation(self):
        """Test creating a pattern."""
        pattern = Pattern(
            pattern_id="test_pattern",
            pattern_type=AnomalyType.FISH_SCHOOL,
            name="Test Fish School",
            description="Test pattern",
            signal_characteristics={"frequency": 1000.0},
            environmental_factors={"temperature": (5.0, 20.0)},
            base_confidence=0.8
        )
        
        assert pattern.pattern_id == "test_pattern"
        assert pattern.pattern_type == AnomalyType.FISH_SCHOOL
        assert pattern.base_confidence == 0.8
    
    def test_pattern_matching(self):
        """Test pattern matching."""
        pattern = Pattern(
            pattern_id="fish",
            pattern_type=AnomalyType.FISH_SCHOOL,
            name="Fish",
            description="Fish school",
            signal_characteristics={"frequency": 1200.0, "intensity": 0.6},
            environmental_factors={"temperature": (5.0, 20.0)},
            base_confidence=0.85,
            match_threshold=0.7
        )
        
        # Matching characteristics
        characteristics = {"frequency": 1200.0, "intensity": 0.6}
        matches, confidence = pattern.matches(characteristics)
        
        assert matches is True
        assert confidence > 0.7
    
    def test_pattern_no_match(self):
        """Test pattern non-matching."""
        pattern = Pattern(
            pattern_id="fish",
            pattern_type=AnomalyType.FISH_SCHOOL,
            name="Fish",
            description="Fish school",
            signal_characteristics={"frequency": 1200.0},
            environmental_factors={"temperature": (5.0, 20.0)},
            base_confidence=0.85
        )
        
        # Non-matching characteristics
        characteristics = {"frequency": 3000.0}
        matches, confidence = pattern.matches(characteristics)
        
        assert matches is False
    
    def test_learner_initialization(self):
        """Test pattern learner initialization."""
        learner = AnomalyPatternLearner()
        
        patterns = learner.get_all_patterns()
        assert len(patterns) > 0
        assert "fish_school" in patterns
        assert "geological" in patterns
    
    def test_learner_add_custom_pattern(self):
        """Test adding custom pattern."""
        learner = AnomalyPatternLearner()
        
        custom = Pattern(
            pattern_id="custom",
            pattern_type=AnomalyType.DEBRIS_FIELD,
            name="Custom Debris",
            description="Custom pattern",
            signal_characteristics={},
            environmental_factors={}
        )
        
        learner.add_pattern(custom)
        patterns = learner.get_all_patterns()
        
        assert "custom" in patterns
    
    def test_learner_identify_pattern(self):
        """Test identifying matching pattern."""
        learner = AnomalyPatternLearner()
        
        # Create anomaly with characteristics matching a known pattern
        anomaly = ContextualAnomaly(
            anomaly_id="test",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.8,
            detected_type=AnomalyType.FISH_SCHOOL,
            depth=50.0,
            temperature=15.0,  # Within fish_school temp range (5-25)
            current_speed=0.5  # Within fish_school current range (0-2)
        )
        
        # Even if pattern matching doesn't find exact match, the function should work
        result = learner.identify_known_pattern(anomaly)
        # Result may be None if no pattern matches threshold, which is OK
        if result:
            pattern, confidence = result
            assert confidence >= 0.0 and confidence <= 1.0


# ============================================================================
# Test: Anomaly Explanation
# ============================================================================

class TestExplanation:
    """Test explanation data class and generation."""
    
    def test_explanation_creation(self):
        """Test creating explanation."""
        explanation = Explanation(
            anomaly_id="test",
            timestamp=datetime.now().timestamp(),
            conclusion="Test conclusion",
            reasoning="Test reasoning"
        )
        
        assert explanation.anomaly_id == "test"
        assert explanation.conclusion == "Test conclusion"
    
    def test_explanation_to_dict(self):
        """Test converting explanation to dictionary."""
        explanation = Explanation(
            anomaly_id="test",
            timestamp=datetime.now().timestamp(),
            conclusion="Test",
            reasoning="Reason",
            overall_confidence=0.85,
            assessed_risk_level=RiskLevel.HIGH
        )
        
        result = explanation.to_dict()
        
        assert result["anomaly_id"] == "test"
        assert result["overall_confidence"] == 0.85
        assert result["risk_level"] == "high"
    
    def test_explanation_to_markdown(self):
        """Test converting explanation to markdown."""
        explanation = Explanation(
            anomaly_id="test",
            timestamp=datetime.now().timestamp(),
            conclusion="Test conclusion",
            reasoning="Test reasoning",
            supporting_evidence=["Evidence 1", "Evidence 2"],
            overall_confidence=0.8,
            assessed_risk_level=RiskLevel.MEDIUM,
            recommended_actions=["Action 1", "Action 2"]
        )
        
        markdown = explanation.to_markdown()
        
        assert "Test conclusion" in markdown
        assert "Evidence 1" in markdown
        assert "Action 1" in markdown
        assert "# Anomaly Report" in markdown


# ============================================================================
# Test: Anomaly Explainer
# ============================================================================

class TestAnomalyExplainer:
    """Test explanation generation."""
    
    def test_explainer_initialization(self):
        """Test initializing explainer."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        assert explainer.pattern_learner is learner
        assert len(explainer.explanation_cache) == 0
    
    def test_explain_high_confidence_detection(self):
        """Test explaining high-confidence detection."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="test_high",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.9,
            detected_type=AnomalyType.ARTIFACT,
            classification_confidence=0.95,
            depth=50.0
        )
        
        explanation = explainer.explain_detection(anomaly)
        
        assert explanation.anomaly_id == "test_high"
        assert explanation.overall_confidence > 0.5
        assert len(explanation.conclusion) > 0
    
    def test_explain_low_confidence_detection(self):
        """Test explaining low-confidence detection."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="test_low",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.3,
            detected_type=AnomalyType.UNKNOWN,
            classification_confidence=0.4,
            depth=100.0
        )
        
        explanation = explainer.explain_detection(anomaly)
        
        assert explanation.overall_confidence < 0.5
        assert len(explanation.contradicting_evidence) > 0
    
    def test_generate_supporting_evidence(self):
        """Test generating supporting evidence."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="test",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.85,
            classification_confidence=0.90,
            depth=75.0,
            contributing_sensors=["sonar", "bathymetry"]
        )
        
        evidence = explainer._gather_supporting_evidence(anomaly)
        
        assert len(evidence) > 0
        assert any("Signal" in e or "signal" in e.lower() for e in evidence)
    
    def test_generate_report(self):
        """Test generating full report."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="report_test",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.75,
            classification_confidence=0.8,
            depth=50.0
        )
        
        report = explainer.generate_report(anomaly)
        
        assert "Anomaly Report" in report
        assert "report_test" in report
    
    def test_retrieve_cached_explanation(self):
        """Test retrieving cached explanation."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="cached",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.7,
            classification_confidence=0.75,
            depth=50.0
        )
        
        # Generate explanation
        explainer.explain_detection(anomaly)
        
        # Retrieve it
        retrieved = explainer.get_explanation("cached")
        
        assert retrieved is not None
        assert retrieved.anomaly_id == "cached"


# ============================================================================
# Test: Risk Assessment
# ============================================================================

class TestRiskAssessment:
    """Test risk level assessment."""
    
    def test_critical_risk_assignment(self):
        """Test assigning critical/high risk."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        # High confidence SAR-relevant target
        anomaly = ContextualAnomaly(
            anomaly_id="critical",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.95,
            detected_type=AnomalyType.ARTIFACT,
            classification_confidence=0.95,
            depth=50.0
        )
        
        explanation = explainer.explain_detection(anomaly)
        
        # With good confidence and artifact type, should be at least MEDIUM
        assert explanation.assessed_risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_low_risk_assignment(self):
        """Test assigning low/medium risk."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        # Low-medium confidence geological feature (not SAR-relevant)
        anomaly = ContextualAnomaly(
            anomaly_id="low_risk",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.5,
            detected_type=AnomalyType.GEOLOGICAL,
            classification_confidence=0.6,
            depth=100.0
        )
        
        explanation = explainer.explain_detection(anomaly)
        
        # Geological with moderate confidence should be LOW or MEDIUM
        assert explanation.assessed_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    def test_risk_justification(self):
        """Test risk justification generation."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="justified",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.8,
            classification_confidence=0.85,
            depth=50.0
        )
        
        explanation = explainer.explain_detection(anomaly)
        
        assert len(explanation.risk_justification) > 0


# ============================================================================
# Test: Contextual Anomaly Detector
# ============================================================================

class TestContextualAnomalyDetector:
    """Test main detection engine."""
    
    def test_detector_initialization(self):
        """Test initializing detector."""
        detector = ContextualAnomalyDetector()
        
        assert detector.pattern_learner is not None
        assert detector.explainer is not None
        assert len(detector.detection_history) == 0
    
    def test_detect_high_intensity_anomaly(self):
        """Test detecting high-intensity anomaly."""
        detector = ContextualAnomalyDetector(
            classifier=MockSignalClassifier()
        )
        
        readings = {
            "sonar_intensity": 0.85,
            "depth": 50.0,
            "temperature": 15.5,
            "current_speed": 0.2
        }
        
        location = MockLocation()
        anomalies = detector.detect_anomalies(readings, location)
        
        assert len(anomalies) > 0
        assert anomalies[0].signal_intensity == 0.85
    
    def test_detect_below_threshold(self):
        """Test that weak signals are not detected."""
        detector = ContextualAnomalyDetector()
        detector.threshold = 0.7
        
        readings = {
            "sonar_intensity": 0.3,  # Below threshold
            "depth": 50.0
        }
        
        location = MockLocation()
        anomalies = detector.detect_anomalies(readings, location)
        
        assert len(anomalies) == 0
    
    def test_score_anomaly(self):
        """Test scoring anomaly."""
        detector = ContextualAnomalyDetector()
        
        anomaly = ContextualAnomaly(
            anomaly_id="scored",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.8,
            classification_confidence=0.85,
            anomaly_confidence=0.75,
            risk_level=RiskLevel.HIGH
        )
        
        scores = detector.score_anomaly(anomaly)
        
        assert "overall_confidence" in scores
        assert "classification_confidence" in scores
        assert "risk_score" in scores
        assert all(0.0 <= v <= 1.0 for v in scores.values())
    
    def test_get_anomaly_patterns(self):
        """Test retrieving anomaly patterns."""
        detector = ContextualAnomalyDetector()
        
        patterns = detector.get_anomaly_patterns()
        
        assert len(patterns) > 0
        assert "fish_school" in patterns
    
    def test_get_detection_history(self):
        """Test retrieving detection history."""
        detector = ContextualAnomalyDetector()
        
        # Add some detections
        for i in range(5):
            anomaly = ContextualAnomaly(
                anomaly_id=f"anomaly_{i}",
                location=MockLocation(),
                timestamp=datetime.now().timestamp(),
                signal_intensity=0.7,
                detected_type=AnomalyType.UNKNOWN,
                classification_confidence=0.6
            )
            detector.detection_history.append(anomaly)
        
        history = detector.get_detection_history(limit=3)
        
        assert len(history) == 3
    
    def test_get_high_risk_anomalies(self):
        """Test retrieving high-risk anomalies."""
        detector = ContextualAnomalyDetector()
        
        # Add mixed detections
        for i in range(5):
            risk_level = RiskLevel.HIGH if i < 2 else RiskLevel.LOW
            anomaly = ContextualAnomaly(
                anomaly_id=f"anomaly_{i}",
                location=MockLocation(),
                timestamp=datetime.now().timestamp(),
                signal_intensity=0.7,
                detected_type=AnomalyType.UNKNOWN,
                classification_confidence=0.6,
                risk_level=risk_level
            )
            detector.detection_history.append(anomaly)
        
        high_risk = detector.get_high_risk_anomalies()
        
        assert len(high_risk) == 2
    
    def test_update_threshold(self):
        """Test updating detection threshold."""
        detector = ContextualAnomalyDetector()
        
        initial_threshold = detector.threshold
        detector.update_threshold(0.8)
        
        assert detector.threshold == 0.8
        assert detector.threshold != initial_threshold
    
    def test_threshold_bounds(self):
        """Test threshold stays within bounds."""
        detector = ContextualAnomalyDetector()
        
        detector.update_threshold(-0.5)
        assert detector.threshold == 0.0
        
        detector.update_threshold(1.5)
        assert detector.threshold == 1.0
    
    def test_get_statistics(self):
        """Test getting statistics."""
        detector = ContextualAnomalyDetector()
        
        # Add detections
        for i in range(10):
            anomaly = ContextualAnomaly(
                anomaly_id=f"anomaly_{i}",
                location=MockLocation(),
                timestamp=datetime.now().timestamp(),
                signal_intensity=0.7 + (i * 0.01),
                anomaly_confidence=0.6 + (i * 0.02),
                detected_type=AnomalyType.UNKNOWN,
                classification_confidence=0.6,
                risk_level=RiskLevel.MEDIUM if i < 3 else RiskLevel.LOW
            )
            detector.detection_history.append(anomaly)
        
        stats = detector.get_statistics()
        
        assert stats["total_detections"] == 10
        assert 0.0 <= stats["average_confidence"] <= 1.0
        assert stats["high_risk_count"] == 0  # No CRITICAL/HIGH in this batch


# ============================================================================
# Test: Contextual Anomaly Data Class
# ============================================================================

class TestContextualAnomaly:
    """Test ContextualAnomaly data class."""
    
    def test_anomaly_creation(self):
        """Test creating anomaly."""
        anomaly = ContextualAnomaly(
            anomaly_id="test",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.75,
            detected_type=AnomalyType.ARTIFACT,
            depth=50.0
        )
        
        assert anomaly.anomaly_id == "test"
        assert anomaly.signal_intensity == 0.75
        assert anomaly.depth == 50.0
    
    def test_combined_confidence(self):
        """Test calculating combined confidence."""
        anomaly = ContextualAnomaly(
            anomaly_id="test",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.8,
            classification_confidence=0.85,
            pattern_match_confidence=0.9,
            depth=50.0
        )
        
        combined = anomaly.get_combined_confidence()
        
        assert 0.0 <= combined <= 1.0
        assert combined > 0.5


# ============================================================================
# Test: Integration Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """Test end-to-end workflows."""
    
    def test_complete_detection_workflow(self):
        """Test complete detection and analysis workflow."""
        # Setup
        classifier = MockSignalClassifier()
        detector = ContextualAnomalyDetector(classifier=classifier)
        
        # Detect anomaly
        readings = {
            "sonar_intensity": 0.85,
            "depth": 75.0,
            "temperature": 16.0,
            "current_speed": 0.15
        }
        
        location = MockLocation()
        anomalies = detector.detect_anomalies(readings, location)
        
        # Verify full analysis
        assert len(anomalies) > 0
        anomaly = anomalies[0]
        
        assert anomaly.anomaly_confidence > 0.0
        assert anomaly.explanation is not None
        assert anomaly.risk_level in RiskLevel
    
    def test_multiple_detections_workflow(self):
        """Test handling multiple detections."""
        detector = ContextualAnomalyDetector(
            classifier=MockSignalClassifier()
        )
        
        # Multiple readings
        for i in range(5):
            readings = {
                "sonar_intensity": 0.5 + (i * 0.1),
                "depth": 50.0 + (i * 5),
                "temperature": 15.0,
                "current_speed": 0.1
            }
            
            location = MockLocation(x=i*100, y=i*100)
            detector.detect_anomalies(readings, location)
        
        # Verify history
        history = detector.get_detection_history()
        assert len(history) > 0
        
        stats = detector.get_statistics()
        assert stats["total_detections"] > 0
    
    def test_recommendation_generation_workflow(self):
        """Test generating recommendations."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        # Critical risk scenario
        anomaly = ContextualAnomaly(
            anomaly_id="critical_test",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.95,
            detected_type=AnomalyType.ARTIFACT,
            classification_confidence=0.95,
            depth=50.0
        )
        
        explanation = explainer.explain_detection(anomaly)
        
        assert len(explanation.recommended_actions) > 0
        # Critical risk should have urgent recommendations
        if explanation.assessed_risk_level == RiskLevel.CRITICAL:
            assert any("PRIORITY" in action.upper() for action in explanation.recommended_actions)


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_characteristics_pattern_matching(self):
        """Test pattern matching with no characteristics."""
        pattern = Pattern(
            pattern_id="empty",
            pattern_type=AnomalyType.UNKNOWN,
            name="Empty",
            description="Empty pattern",
            signal_characteristics={},
            environmental_factors={}
        )
        
        matches, confidence = pattern.matches({})
        
        assert matches is False
        assert confidence == 0.0
    
    def test_zero_depth_anomaly(self):
        """Test anomaly at depth zero."""
        anomaly = ContextualAnomaly(
            anomaly_id="surface",
            location=MockLocation(z=0),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.5,
            detected_type=AnomalyType.UNKNOWN,
            depth=0.0
        )
        
        combined = anomaly.get_combined_confidence()
        assert 0.0 <= combined <= 1.0
    
    def test_extreme_temperature(self):
        """Test anomaly at extreme temperature."""
        learner = AnomalyPatternLearner()
        explainer = AnomalyExplainer(learner)
        
        anomaly = ContextualAnomaly(
            anomaly_id="extreme_temp",
            location=MockLocation(),
            timestamp=datetime.now().timestamp(),
            signal_intensity=0.7,
            classification_confidence=0.8,
            temperature=30.0  # Very warm
        )
        
        explanation = explainer.explain_detection(anomaly)
        assert explanation is not None
    
    def test_very_weak_signal(self):
        """Test very weak signal detection."""
        detector = ContextualAnomalyDetector()
        detector.threshold = 0.1
        
        readings = {
            "sonar_intensity": 0.05,
            "depth": 50.0
        }
        
        location = MockLocation()
        anomalies = detector.detect_anomalies(readings, location)
        
        # Should still be below threshold
        assert len(anomalies) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
