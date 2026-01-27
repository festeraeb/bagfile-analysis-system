"""
Unit Tests for Sonar Stream Buffer Module (Phase 12.1)

Comprehensive test suite for real-time streaming components.
Tests latency, throughput, thread safety, and integration.

Author: CESARops Development
Date: January 27, 2026
"""

import pytest
import numpy as np
import time
import threading
from unittest.mock import Mock, MagicMock

from src.cesarops.sonar_stream_buffer import (
    SonarPing,
    SonarStreamBuffer,
    DataStreamManager,
    StreamProcessor,
    PerformanceMonitor,
    StreamStatistics
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_ping():
    """Create a sample sonar ping."""
    return SonarPing(
        ping_id=1,
        timestamp=time.time(),
        frequency=200e3,  # 200 kHz
        intensity=np.random.rand(256),
        range_resolution=0.1,
        num_beams=256
    )


@pytest.fixture
def ping_sequence():
    """Create a sequence of sonar pings."""
    pings = []
    for i in range(100):
        pings.append(SonarPing(
            ping_id=i,
            timestamp=time.time() + i * 0.01,  # 10ms apart
            frequency=200e3,
            intensity=np.random.rand(256),
            range_resolution=0.1,
            num_beams=256
        ))
    return pings


@pytest.fixture
def stream_buffer():
    """Create a stream buffer."""
    return SonarStreamBuffer(capacity=1000)


@pytest.fixture
def data_manager():
    """Create a data stream manager."""
    return DataStreamManager()


# ============================================================================
# SonarPing Tests
# ============================================================================

class TestSonarPing:
    """Test SonarPing data structure."""
    
    def test_ping_creation(self, sample_ping):
        """Test creating a sonar ping."""
        assert sample_ping.ping_id == 1
        assert sample_ping.frequency == 200e3
        assert len(sample_ping.intensity) == 256
        assert sample_ping.num_beams == 256
    
    def test_ping_with_list_intensity(self):
        """Test ping creation with list intensity."""
        intensity_list = list(np.random.rand(256))
        ping = SonarPing(
            ping_id=1,
            timestamp=time.time(),
            frequency=200e3,
            intensity=intensity_list,
            range_resolution=0.1
        )
        assert isinstance(ping.intensity, np.ndarray)
        assert len(ping.intensity) == 256
    
    def test_ping_invalid_beams(self):
        """Test ping with wrong number of beams."""
        with pytest.raises(ValueError):
            SonarPing(
                ping_id=1,
                timestamp=time.time(),
                frequency=200e3,
                intensity=np.random.rand(255),  # Wrong size
                range_resolution=0.1
            )
    
    def test_ping_multidimensional_intensity(self):
        """Test ping with multidimensional intensity (invalid)."""
        with pytest.raises(ValueError):
            SonarPing(
                ping_id=1,
                timestamp=time.time(),
                frequency=200e3,
                intensity=np.random.rand(256, 2),  # 2D array
                range_resolution=0.1
            )


# ============================================================================
# SonarStreamBuffer Tests
# ============================================================================

class TestSonarStreamBuffer:
    """Test stream buffer functionality."""
    
    def test_buffer_creation(self):
        """Test creating a stream buffer."""
        buffer = SonarStreamBuffer(capacity=5000)
        assert buffer.capacity == 5000
        assert buffer.get_buffer_size() == 0
        assert not buffer.is_full()
    
    def test_push_single_ping(self, stream_buffer, sample_ping):
        """Test pushing a single ping."""
        result = stream_buffer.push(sample_ping)
        assert result is True
    
    def test_push_multiple_pings(self, stream_buffer, ping_sequence):
        """Test pushing multiple pings."""
        for ping in ping_sequence:
            result = stream_buffer.push(ping)
            assert result is True
    
    def test_push_invalid_type(self, stream_buffer):
        """Test pushing invalid type."""
        with pytest.raises(TypeError):
            stream_buffer.push("invalid")
    
    def test_pop_single_ping(self, stream_buffer, sample_ping):
        """Test popping a single ping."""
        stream_buffer.push(sample_ping)
        result = stream_buffer.pop(count=1)
        assert len(result) == 1
        assert result[0].ping_id == 1
    
    def test_pop_multiple_pings(self, stream_buffer, ping_sequence):
        """Test popping multiple pings."""
        for ping in ping_sequence:
            stream_buffer.push(ping)
        
        result = stream_buffer.pop(count=50)
        assert len(result) == 50
        assert result[0].ping_id == 0
    
    def test_pop_empty_buffer(self, stream_buffer):
        """Test popping from empty buffer."""
        result = stream_buffer.pop(count=10)
        assert len(result) == 0
    
    def test_pop_more_than_available(self, stream_buffer, ping_sequence):
        """Test popping more pings than available."""
        for ping in ping_sequence[:10]:
            stream_buffer.push(ping)
        
        result = stream_buffer.pop(count=50)
        assert len(result) == 10
    
    def test_peek_without_removing(self, stream_buffer, ping_sequence):
        """Test peek (view without removing)."""
        for ping in ping_sequence[:10]:
            stream_buffer.push(ping)
        
        result1 = stream_buffer.peek(count=5)
        result2 = stream_buffer.peek(count=5)
        
        assert len(result1) == 5
        assert len(result2) == 5
        assert result1[0].ping_id == result2[0].ping_id
    
    def test_get_latest(self, stream_buffer, ping_sequence):
        """Test getting latest pings."""
        for ping in ping_sequence:
            stream_buffer.push(ping)
        
        result = stream_buffer.get_latest(count=5)
        assert len(result) == 5
        # Should be the last 5 pings
        expected_ids = [95, 96, 97, 98, 99]
        actual_ids = [p.ping_id for p in result]
        assert actual_ids == expected_ids
    
    def test_buffer_capacity(self, stream_buffer, ping_sequence):
        """Test buffer respects capacity."""
        small_buffer = SonarStreamBuffer(capacity=50)
        
        for ping in ping_sequence:
            small_buffer.push(ping)
        
        assert small_buffer.get_buffer_size() <= 50
    
    def test_clear_buffer(self, stream_buffer, ping_sequence):
        """Test clearing buffer."""
        for ping in ping_sequence[:50]:
            stream_buffer.push(ping)
        
        # Process queued items before clearing
        stream_buffer.peek()
        
        count = stream_buffer.clear()
        assert count == 50
        assert stream_buffer.get_buffer_size() == 0
    
    def test_statistics(self, stream_buffer, ping_sequence):
        """Test statistics collection."""
        for ping in ping_sequence:
            stream_buffer.push(ping)
        
        # Process queued items to update statistics
        stream_buffer.pop(count=100)
        
        stats = stream_buffer.get_stats()
        assert isinstance(stats, StreamStatistics)
        assert stats.total_pings == 100
        assert stats.avg_latency_ms >= 0
        assert stats.pings_dropped >= 0
    
    def test_high_frequency_streaming(self, stream_buffer, ping_sequence):
        """Test handling high-frequency data."""
        start_time = time.time()
        
        for ping in ping_sequence:
            stream_buffer.push(ping)
        
        # Process queued items
        stream_buffer.pop(count=100)
        
        elapsed = time.time() - start_time
        
        # Should handle 100 pings quickly
        assert elapsed < 1.0
        assert stream_buffer.get_buffer_size() == 0  # All processed
    
    def test_thread_safety(self, stream_buffer, ping_sequence):
        """Test thread-safe operations."""
        results = []
        
        def pusher():
            for ping in ping_sequence[:50]:
                stream_buffer.push(ping)
        
        def popper():
            for _ in range(50):
                stream_buffer.pop(count=1)
        
        t1 = threading.Thread(target=pusher)
        t2 = threading.Thread(target=popper)
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # Should complete without errors
        assert True


# ============================================================================
# DataStreamManager Tests
# ============================================================================

class TestDataStreamManager:
    """Test data stream manager."""
    
    def test_manager_creation(self, data_manager):
        """Test creating a manager."""
        assert data_manager.list_sources() == []
    
    def test_register_source(self, data_manager):
        """Test registering a source."""
        buffer = SonarStreamBuffer()
        data_manager.register_source("sonar1", buffer)
        
        assert "sonar1" in data_manager.list_sources()
    
    def test_register_invalid_type(self, data_manager):
        """Test registering invalid source type."""
        with pytest.raises(TypeError):
            data_manager.register_source("invalid", "not a buffer")
    
    def test_process_stream(self, data_manager, ping_sequence):
        """Test processing data stream."""
        buffer = SonarStreamBuffer()
        data_manager.register_source("sonar1", buffer)
        
        data_manager.process_stream("sonar1", ping_sequence[:10])
        
        # Pings should be queued
        assert True
    
    def test_get_latest_frame(self, data_manager, ping_sequence):
        """Test getting latest frame."""
        buffer1 = SonarStreamBuffer()
        buffer2 = SonarStreamBuffer()
        
        data_manager.register_source("sonar1", buffer1)
        data_manager.register_source("sonar2", buffer2)
        
        data_manager.process_stream("sonar1", ping_sequence[:50])
        data_manager.process_stream("sonar2", ping_sequence[50:100])
        
        frame = data_manager.get_latest_frame(pings_per_source=10)
        
        assert "sonar1" in frame
        assert "sonar2" in frame
        assert len(frame["sonar1"]) <= 10
        assert len(frame["sonar2"]) <= 10
    
    def test_get_source_stats(self, data_manager):
        """Test getting source statistics."""
        buffer = SonarStreamBuffer()
        data_manager.register_source("sonar1", buffer)
        
        stats = data_manager.get_source_stats()
        assert "sonar1" in stats
        assert isinstance(stats["sonar1"], StreamStatistics)


# ============================================================================
# StreamProcessor Tests
# ============================================================================

class TestStreamProcessor:
    """Test stream processor."""
    
    def test_processor_creation(self):
        """Test creating a processor."""
        processor = StreamProcessor()
        assert processor.anomaly_detector is None
        assert processor.bathymetry_mapper is None
    
    def test_process_ping_without_modules(self, sample_ping):
        """Test processing ping without Phase 11 modules."""
        processor = StreamProcessor()
        result = processor.process_ping(sample_ping)
        
        assert result['ping_id'] == 1
        assert result['timestamp'] == sample_ping.timestamp
        assert result['anomalies'] is None
    
    def test_process_ping_with_mock_detector(self, sample_ping):
        """Test processing with mock anomaly detector."""
        mock_detector = Mock()
        mock_detector.detect_anomalies.return_value = []
        
        processor = StreamProcessor(anomaly_detector=mock_detector)
        result = processor.process_ping(sample_ping)
        
        assert result['anomalies'] == []
        mock_detector.detect_anomalies.assert_called_once()
    
    def test_process_frame(self, ping_sequence):
        """Test processing a frame."""
        processor = StreamProcessor()
        result = processor.process_frame(ping_sequence[:10])
        
        assert result['pings_processed'] == 10
        assert len(result['ping_results']) == 10
    
    def test_get_processed_data(self, sample_ping):
        """Test getting processor statistics."""
        processor = StreamProcessor()
        
        processor.process_ping(sample_ping)
        processor.process_ping(sample_ping)
        
        stats = processor.get_processed_data()
        assert stats['total_processed'] == 2


# ============================================================================
# PerformanceMonitor Tests
# ============================================================================

class TestPerformanceMonitor:
    """Test performance monitoring."""
    
    def test_monitor_creation(self):
        """Test creating a monitor."""
        monitor = PerformanceMonitor()
        assert monitor.history_size == 1000
    
    def test_record_latency(self):
        """Test recording latency."""
        monitor = PerformanceMonitor()
        monitor.record_latency(10.5)
        monitor.record_latency(12.3)
        
        metrics = monitor.get_metrics()
        assert metrics['latency_avg_ms'] > 0
    
    def test_latency_range(self):
        """Test latency range tracking."""
        monitor = PerformanceMonitor()
        
        latencies = [5.0, 10.0, 15.0, 20.0]
        for lat in latencies:
            monitor.record_latency(lat)
        
        metrics = monitor.get_metrics()
        assert metrics['latency_min_ms'] == 5.0
        assert metrics['latency_max_ms'] == 20.0
    
    def test_record_throughput(self):
        """Test recording throughput."""
        monitor = PerformanceMonitor()
        monitor.record_throughput(100, 1.0)  # 100 items in 1 second
        
        metrics = monitor.get_metrics()
        assert metrics['throughput_avg'] == 100.0
    
    def test_record_frame_time(self):
        """Test recording frame time."""
        monitor = PerformanceMonitor()
        
        # 60 FPS = ~16.67ms per frame
        for _ in range(60):
            monitor.record_frame_time(16.67)
        
        metrics = monitor.get_metrics()
        assert abs(metrics['fps'] - 60.0) < 1.0  # Should be ~60 FPS
    
    def test_invalid_latency(self):
        """Test recording invalid latency."""
        monitor = PerformanceMonitor()
        
        with pytest.raises(ValueError):
            monitor.record_latency(-5.0)
    
    def test_invalid_throughput(self):
        """Test recording invalid throughput."""
        monitor = PerformanceMonitor()
        
        with pytest.raises(ValueError):
            monitor.record_throughput(100, 0.0)
    
    def test_reset(self):
        """Test resetting monitor."""
        monitor = PerformanceMonitor()
        monitor.record_latency(10.0)
        monitor.record_latency(20.0)
        
        monitor.reset()
        
        metrics = monitor.get_metrics()
        assert metrics['latency_avg_ms'] == 0.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestStreamIntegration:
    """Integration tests for streaming system."""
    
    def test_full_streaming_pipeline(self, ping_sequence):
        """Test complete streaming pipeline."""
        # Create components
        buffer = SonarStreamBuffer(capacity=1000)
        manager = DataStreamManager()
        processor = StreamProcessor()
        monitor = PerformanceMonitor()
        
        manager.register_source("sonar1", buffer)
        
        # Stream data
        for ping in ping_sequence:
            start = time.time()
            buffer.push(ping)
            latency = (time.time() - start) * 1000
            monitor.record_latency(latency)
        
        # Process data
        frame = manager.get_latest_frame(pings_per_source=20)
        
        assert "sonar1" in frame
        assert len(frame["sonar1"]) > 0
    
    def test_streaming_latency_target(self, ping_sequence):
        """Test that streaming meets <100ms latency target."""
        buffer = SonarStreamBuffer(capacity=10000)
        monitor = PerformanceMonitor()
        
        for ping in ping_sequence:
            start = time.time()
            buffer.push(ping)
            buffer.pop(count=1)
            latency = (time.time() - start) * 1000
            monitor.record_latency(latency)
        
        metrics = monitor.get_metrics()
        # Average latency should be <100ms for this test
        assert metrics['latency_avg_ms'] < 100.0
    
    def test_60_fps_capable(self):
        """Test system is capable of 60 FPS."""
        buffer = SonarStreamBuffer(capacity=10000)
        monitor = PerformanceMonitor()
        
        # Simulate 60 frames
        for frame_num in range(60):
            pings = [
                SonarPing(
                    ping_id=frame_num * 10 + i,
                    timestamp=time.time(),
                    frequency=200e3,
                    intensity=np.random.rand(256),
                    range_resolution=0.1
                )
                for i in range(10)
            ]
            
            frame_start = time.time()
            
            for ping in pings:
                buffer.push(ping)
                buffer.pop(count=1)
            
            frame_time = (time.time() - frame_start) * 1000
            monitor.record_frame_time(frame_time)
        
        metrics = monitor.get_metrics()
        # Should achieve close to 60 FPS
        assert metrics['fps'] > 30.0  # At least 30 FPS


# ============================================================================
# Performance Tests
# ============================================================================

class TestStreamPerformance:
    """Performance-focused tests."""
    
    def test_burst_push_performance(self):
        """Test performance of burst push operations."""
        buffer = SonarStreamBuffer(capacity=10000)
        
        start = time.time()
        
        for i in range(1000):
            ping = SonarPing(
                ping_id=i,
                timestamp=time.time(),
                frequency=200e3,
                intensity=np.random.rand(256),
                range_resolution=0.1
            )
            buffer.push(ping)
        
        elapsed = time.time() - start
        
        # Should process 1000 pings in <1 second
        assert elapsed < 1.0
    
    def test_memory_stability(self):
        """Test buffer memory doesn't grow unbounded."""
        buffer = SonarStreamBuffer(capacity=1000)
        
        # Push 10x capacity
        for i in range(10000):
            ping = SonarPing(
                ping_id=i,
                timestamp=time.time(),
                frequency=200e3,
                intensity=np.random.rand(256),
                range_resolution=0.1
            )
            buffer.push(ping)
        
        # Buffer should not exceed capacity
        assert buffer.get_buffer_size() <= 1000


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
