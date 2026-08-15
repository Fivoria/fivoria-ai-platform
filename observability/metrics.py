"""
Fivoria AI Observability System
Metrics collection and monitoring
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
from enum import Enum


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class Counter:
    """Counter metric - monotonically increasing"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._labels: Dict[tuple, float] = defaultdict(float)
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter"""
        if labels:
            key = tuple(sorted(labels.items()))
            self._labels[key] += value
        else:
            self._value += value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        if labels:
            key = tuple(sorted(labels.items()))
            return self._labels.get(key, 0.0)
        return self._value
    
    def reset(self):
        """Reset counter"""
        self._value = 0.0
        self._labels.clear()


class Gauge:
    """Gauge metric - can go up or down"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._labels: Dict[tuple, float] = defaultdict(float)
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value"""
        if labels:
            key = tuple(sorted(labels.items()))
            self._labels[key] = value
        else:
            self._value = value
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        if labels:
            key = tuple(sorted(labels.items()))
            self._labels[key] += value
        else:
            self._value += value
    
    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        if labels:
            key = tuple(sorted(labels.items()))
            self._labels[key] -= value
        else:
            self._value -= value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        if labels:
            key = tuple(sorted(labels.items()))
            return self._labels.get(key, 0.0)
        return self._value


class Histogram:
    """Histogram metric - distribution of values"""
    
    def __init__(
        self,
        name: str,
        buckets: Optional[List[float]] = None,
        description: str = ""
    ):
        self.name = name
        self.description = description
        self.buckets = buckets or [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]
        self._samples: List[float] = []
        self._labels: Dict[tuple, List[float]] = defaultdict(list)
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        if labels:
            key = tuple(sorted(labels.items()))
            self._labels[key].append(value)
        else:
            self._samples.append(value)
    
    def get_buckets(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, int]:
        """Get bucket counts"""
        samples = self._labels.get(tuple(sorted(labels.items()))) if labels else self._samples
        
        bucket_counts = {f"le_{b}": 0 for b in self.buckets}
        bucket_counts["le_inf"] = len(samples)
        
        for sample in samples:
            for bucket in self.buckets:
                if sample <= bucket:
                    bucket_counts[f"le_{bucket}"] += 1
        
        return bucket_counts
    
    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get total count"""
        samples = self._labels.get(tuple(sorted(labels.items()))) if labels else self._samples
        return len(samples)
    
    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of values"""
        samples = self._labels.get(tuple(sorted(labels.items()))) if labels else self._samples
        return sum(samples)


class Summary:
    """Summary metric - quantiles"""
    
    def __init__(
        self,
        name: str,
        quantiles: Optional[List[float]] = None,
        max_age_seconds: int = 600,
        description: str = ""
    ):
        self.name = name
        self.description = description
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self.max_age_seconds = max_age_seconds
        self._samples: deque = deque()
        self._labels: Dict[tuple, deque] = defaultdict(deque)
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        now = datetime.utcnow()
        
        if labels:
            key = tuple(sorted(labels.items()))
            self._labels[key].append((value, now))
        else:
            self._samples.append((value, now))
    
    def get_quantiles(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get quantile values"""
        samples = self._labels.get(tuple(sorted(labels.items()))) if labels else self._samples
        
        # Clean old samples
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.max_age_seconds)
        samples = deque([s for s in samples if s[1] > cutoff])
        
        if not samples:
            return {f"p{int(q*100)}": 0.0 for q in self.quantiles}
        
        values = sorted([s[0] for s in samples])
        n = len(values)
        
        quantile_values = {}
        for q in self.quantiles:
            index = int(q * n)
            if index >= n:
                index = n - 1
            quantile_values[f"p{int(q*100)}"] = values[index]
        
        return quantile_values
    
    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get count of samples"""
        samples = self._labels.get(tuple(sorted(labels.items()))) if labels else self._samples
        return len(samples)


class MetricsRegistry:
    """Central metrics registry"""
    
    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        self._lock = threading.Lock()
    
    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create counter"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create gauge"""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]
    
    def histogram(self, name: str, buckets: Optional[List[float]] = None, description: str = "") -> Histogram:
        """Get or create histogram"""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, buckets, description)
            return self._histograms[name]
    
    def summary(self, name: str, quantiles: Optional[List[float]] = None, description: str = "") -> Summary:
        """Get or create summary"""
        with self._lock:
            if name not in self._summaries:
                self._summaries[name] = Summary(name, quantiles, description=description)
            return self._summaries[name]
    
    def get_all_metrics(self) -> List[Dict]:
        """Get all metrics for export"""
        metrics = []
        
        # Counters
        for name, counter in self._counters.items():
            metrics.append({
                "name": name,
                "type": "counter",
                "value": counter.get(),
                "description": counter.description
            })
        
        # Gauges
        for name, gauge in self._gauges.items():
            metrics.append({
                "name": name,
                "type": "gauge",
                "value": gauge.get(),
                "description": gauge.description
            })
        
        # Histograms
        for name, histogram in self._histograms.items():
            metrics.append({
                "name": name,
                "type": "histogram",
                "count": histogram.get_count(),
                "sum": histogram.get_sum(),
                "buckets": histogram.get_buckets(),
                "description": histogram.description
            })
        
        # Summaries
        for name, summary in self._summaries.items():
            metrics.append({
                "name": name,
                "type": "summary",
                "count": summary.get_count(),
                "quantiles": summary.get_quantiles(),
                "description": summary.description
            })
        
        return metrics
    
    def reset_all(self):
        """Reset all metrics"""
        with self._lock:
            for counter in self._counters.values():
                counter.reset()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()


class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self._latency_histogram = registry.histogram(
            "request_latency_seconds",
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
        self._request_counter = registry.counter("request_total")
        self._error_counter = registry.counter("error_total")
        self._active_requests = registry.gauge("active_requests")
    
    def track_request(self, operation: str):
        """Context manager for tracking requests"""
        return RequestTracker(self, operation)


class RequestTracker:
    """Context manager for tracking individual requests"""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = None
        self.success = False
    
    def __enter__(self):
        self.monitor._active_requests.inc()
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor._active_requests.dec()
        
        if self.start_time:
            latency = time.time() - self.start_time
            self.monitor._latency_histogram.observe(latency, labels={"operation": self.operation})
        
        self.monitor._request_counter.inc(labels={"operation": self.operation})
        
        if exc_type is not None:
            self.monitor._error_counter.inc(labels={"operation": self.operation, "error": str(exc_type)})
            self.success = False
        else:
            self.success = True


class GPUMonitor:
    """GPU monitoring metrics"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self._gpu_utilization = registry.gauge("gpu_utilization_percent")
        self._gpu_memory_used = registry.gauge("gpu_memory_used_mb")
        self._gpu_memory_total = registry.gauge("gpu_memory_total_mb")
        self._gpu_temperature = registry.gauge("gpu_temperature_celsius")
        self._gpu_power_usage = registry.gauge("gpu_power_usage_watts")
    
    def record_gpu_stats(
        self,
        gpu_id: int,
        utilization: float,
        memory_used: float,
        memory_total: float,
        temperature: float,
        power_usage: float
    ):
        """Record GPU statistics"""
        labels = {"gpu_id": str(gpu_id)}
        self._gpu_utilization.set(utilization, labels)
        self._gpu_memory_used.set(memory_used, labels)
        self._gpu_memory_total.set(memory_total, labels)
        self._gpu_temperature.set(temperature, labels)
        self._gpu_power_usage.set(power_usage, labels)


class TrainingMonitor:
    """Training-specific metrics"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self._training_loss = registry.gauge("training_loss")
        self._validation_loss = registry.gauge("validation_loss")
        self._tokens_per_second = registry.gauge("tokens_per_second")
        self._gpu_memory_usage = registry.gauge("training_gpu_memory_gb")
        self._gradient_norm = registry.histogram("gradient_norm")
        self._learning_rate = registry.gauge("learning_rate")
        self._checkpoint_duration = registry.summary("checkpoint_duration_seconds")
    
    def record_training_step(
        self,
        step: int,
        loss: float,
        tokens_per_second: float,
        gpu_memory_gb: float,
        gradient_norm: float,
        learning_rate: float
    ):
        """Record training step metrics"""
        self._training_loss.set(loss, labels={"step": str(step)})
        self._tokens_per_second.set(tokens_per_second)
        self._gpu_memory_usage.set(gpu_memory_gb)
        self._gradient_norm.observe(gradient_norm)
        self._learning_rate.set(learning_rate)
    
    def record_validation(self, step: int, loss: float):
        """Record validation metrics"""
        self._validation_loss.set(loss, labels={"step": str(step)})
    
    def record_checkpoint(self, duration_seconds: float):
        """Record checkpoint duration"""
        self._checkpoint_duration.observe(duration_seconds)


class InferenceMonitor:
    """Inference-specific metrics"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self._inference_latency = registry.histogram("inference_latency_seconds")
        self._tokens_generated = registry.counter("tokens_generated_total")
        self._tokens_input = registry.counter("tokens_input_total")
        self._throughput = registry.gauge("inference_tokens_per_second")
        self._queue_size = registry.gauge("inference_queue_size")
        self._model_load_time = registry.summary("model_load_time_seconds")
    
    def record_inference(
        self,
        latency: float,
        input_tokens: int,
        output_tokens: int,
        model_name: str
    ):
        """Record inference metrics"""
        self._inference_latency.observe(latency, labels={"model": model_name})
        self._tokens_input.inc(input_tokens, labels={"model": model_name})
        self._tokens_generated.inc(output_tokens, labels={"model": model_name})
        
        if latency > 0:
            throughput = (input_tokens + output_tokens) / latency
            self._throughput.set(throughput, labels={"model": model_name})
    
    def record_queue_size(self, size: int):
        """Record queue size"""
        self._queue_size.set(size)
    
    def record_model_load(self, duration_seconds: float, model_name: str):
        """Record model load time"""
        self._model_load_time.observe(duration_seconds, labels={"model": model_name})


# Global registry
registry = MetricsRegistry()

# Predefined monitors
performance = PerformanceMonitor(registry)
gpu_monitor = GPUMonitor(registry)
training_monitor = TrainingMonitor(registry)
inference_monitor = InferenceMonitor(registry)


if __name__ == "__main__":
    # Demo: Metrics collection
    print("Fivoria AI Observability System Demo")
    print("=" * 50)
    
    # Track some requests
    with performance.track_request("chat_completion"):
        time.sleep(0.05)  # Simulate work
    
    with performance.track_request("embedding"):
        time.sleep(0.02)  # Simulate work
    
    # Record GPU stats
    gpu_monitor.record_gpu_stats(
        gpu_id=0,
        utilization=85.5,
        memory_used=40960,
        memory_total=81920,
        temperature=72,
        power_usage=350
    )
    
    # Record training step
    training_monitor.record_training_step(
        step=1000,
        loss=2.345,
        tokens_per_second=50000,
        gpu_memory_gb=40,
        gradient_norm=1.5,
        learning_rate=0.0001
    )
    
    # Record inference
    inference_monitor.record_inference(
        latency=0.15,
        input_tokens=100,
        output_tokens=50,
        model_name="fivoria-7b"
    )
    
    # Get all metrics
    metrics = registry.get_all_metrics()
    
    print(f"\nTotal metrics: {len(metrics)}")
    print("\nMetrics summary:")
    for metric in metrics:
        print(f"  {metric['name']} ({metric['type']})")
        if metric['type'] == 'counter':
            print(f"    Value: {metric['value']}")
        elif metric['type'] == 'gauge':
            print(f"    Value: {metric['value']}")
        elif metric['type'] == 'histogram':
            print(f"    Count: {metric['count']}, Sum: {metric['sum']}")
        elif metric['type'] == 'summary':
            print(f"    Count: {metric['count']}, Quantiles: {metric['quantiles']}")
