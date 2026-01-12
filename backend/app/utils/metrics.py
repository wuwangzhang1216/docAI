"""
Performance Metrics and Monitoring Utilities.

Provides tools for tracking and analyzing application performance.
Designed for integration with monitoring systems (Prometheus, CloudWatch, etc.)
"""

import time
import functools
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from contextlib import contextmanager
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric measurement."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    name: str
    count: int
    total: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float
    error_count: int = 0
    error_rate: float = 0.0


class MetricsCollector:
    """
    Collects and aggregates application metrics.

    Supports:
    - Request latency tracking
    - Error rate monitoring
    - Custom metric recording
    - Percentile calculations
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum number of data points to keep in memory
        """
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._errors: Dict[str, int] = defaultdict(int)
        self._max_history = max_history
        self._start_time = datetime.utcnow()

    def record(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels/tags
        """
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            labels=labels or {}
        )

        self._metrics[name].append(point)

        # Trim if over max history
        if len(self._metrics[name]) > self._max_history:
            self._metrics[name] = self._metrics[name][-self._max_history:]

    def record_error(self, name: str) -> None:
        """Record an error for a metric."""
        self._errors[name] += 1

    def get_summary(self, name: str, window_minutes: int = 5) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.

        Args:
            name: Metric name
            window_minutes: Time window in minutes

        Returns:
            MetricSummary or None if no data
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        values = [
            p.value for p in self._metrics.get(name, [])
            if p.timestamp >= cutoff
        ]

        if not values:
            return None

        sorted_values = sorted(values)
        count = len(values)

        return MetricSummary(
            name=name,
            count=count,
            total=sum(values),
            min=min(values),
            max=max(values),
            avg=statistics.mean(values),
            p50=sorted_values[int(count * 0.5)] if count > 0 else 0,
            p95=sorted_values[int(count * 0.95)] if count > 1 else sorted_values[-1],
            p99=sorted_values[int(count * 0.99)] if count > 1 else sorted_values[-1],
            error_count=self._errors.get(name, 0),
            error_rate=self._errors.get(name, 0) / max(count, 1)
        )

    def get_all_summaries(self, window_minutes: int = 5) -> List[MetricSummary]:
        """Get summaries for all metrics."""
        summaries = []
        for name in self._metrics.keys():
            summary = self.get_summary(name, window_minutes)
            if summary:
                summaries.append(summary)
        return summaries

    @contextmanager
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.

        Usage:
            with metrics.timer("db_query"):
                result = await db.execute(query)
        """
        start = time.perf_counter()
        error_occurred = False
        try:
            yield
        except Exception:
            error_occurred = True
            self.record_error(name)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.record(name, elapsed_ms, labels)

    def timed(self, name: Optional[str] = None):
        """
        Decorator for timing function execution.

        Usage:
            @metrics.timed("my_function")
            async def my_function():
                ...
        """
        def decorator(func: Callable) -> Callable:
            metric_name = name or f"{func.__module__}.{func.__name__}"

            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    try:
                        return await func(*args, **kwargs)
                    except Exception:
                        self.record_error(metric_name)
                        raise
                    finally:
                        elapsed_ms = (time.perf_counter() - start) * 1000
                        self.record(metric_name, elapsed_ms)
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        self.record_error(metric_name)
                        raise
                    finally:
                        elapsed_ms = (time.perf_counter() - start) * 1000
                        self.record(metric_name, elapsed_ms)
                return sync_wrapper
        return decorator

    def get_uptime(self) -> timedelta:
        """Get application uptime."""
        return datetime.utcnow() - self._start_time

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._errors.clear()

    def to_dict(self, window_minutes: int = 5) -> Dict[str, Any]:
        """
        Export metrics as dictionary.

        Useful for JSON serialization and API endpoints.
        """
        summaries = self.get_all_summaries(window_minutes)

        return {
            "uptime_seconds": self.get_uptime().total_seconds(),
            "window_minutes": window_minutes,
            "metrics": [
                {
                    "name": s.name,
                    "count": s.count,
                    "avg_ms": round(s.avg, 2),
                    "p50_ms": round(s.p50, 2),
                    "p95_ms": round(s.p95, 2),
                    "p99_ms": round(s.p99, 2),
                    "min_ms": round(s.min, 2),
                    "max_ms": round(s.max, 2),
                    "error_rate": round(s.error_rate * 100, 2)
                }
                for s in summaries
            ]
        }


class RequestMetrics:
    """
    Specialized metrics for HTTP request tracking.

    Tracks:
    - Request count by endpoint
    - Response time by endpoint
    - Status code distribution
    - Error rates
    """

    def __init__(self):
        self._collector = MetricsCollector()
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._status_codes: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float
    ) -> None:
        """
        Record an HTTP request.

        Args:
            endpoint: Request endpoint (e.g., "/api/v1/auth/login")
            method: HTTP method (GET, POST, etc.)
            status_code: Response status code
            duration_ms: Request duration in milliseconds
        """
        metric_name = f"{method}:{endpoint}"

        self._collector.record(metric_name, duration_ms)
        self._request_counts[metric_name] += 1
        self._status_codes[metric_name][status_code] += 1

        if status_code >= 400:
            self._collector.record_error(metric_name)

    def get_endpoint_stats(
        self,
        endpoint: str,
        method: str,
        window_minutes: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific endpoint."""
        metric_name = f"{method}:{endpoint}"
        summary = self._collector.get_summary(metric_name, window_minutes)

        if not summary:
            return None

        return {
            "endpoint": endpoint,
            "method": method,
            "total_requests": self._request_counts[metric_name],
            "avg_response_time_ms": round(summary.avg, 2),
            "p95_response_time_ms": round(summary.p95, 2),
            "error_rate": round(summary.error_rate * 100, 2),
            "status_codes": dict(self._status_codes[metric_name])
        }

    def get_all_stats(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get statistics for all endpoints."""
        stats = {
            "window_minutes": window_minutes,
            "total_requests": sum(self._request_counts.values()),
            "endpoints": []
        }

        for metric_name in self._request_counts.keys():
            method, endpoint = metric_name.split(":", 1)
            endpoint_stats = self.get_endpoint_stats(endpoint, method, window_minutes)
            if endpoint_stats:
                stats["endpoints"].append(endpoint_stats)

        # Sort by request count descending
        stats["endpoints"].sort(key=lambda x: x["total_requests"], reverse=True)

        return stats


class DatabaseMetrics:
    """
    Specialized metrics for database operations.

    Tracks:
    - Query execution time
    - Connection pool usage
    - Slow queries
    """

    SLOW_QUERY_THRESHOLD_MS = 100

    def __init__(self):
        self._collector = MetricsCollector()
        self._slow_queries: List[Dict[str, Any]] = []
        self._query_counts: Dict[str, int] = defaultdict(int)

    def record_query(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        rows_affected: int = 0
    ) -> None:
        """
        Record a database query.

        Args:
            operation: Query type (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
        """
        metric_name = f"db:{operation}:{table}"
        self._collector.record(metric_name, duration_ms)
        self._query_counts[metric_name] += 1

        # Track slow queries
        if duration_ms > self.SLOW_QUERY_THRESHOLD_MS:
            self._slow_queries.append({
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation,
                "table": table,
                "duration_ms": round(duration_ms, 2),
                "rows_affected": rows_affected
            })

            # Keep only last 100 slow queries
            if len(self._slow_queries) > 100:
                self._slow_queries = self._slow_queries[-100:]

    def get_stats(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get database metrics summary."""
        summaries = self._collector.get_all_summaries(window_minutes)

        return {
            "window_minutes": window_minutes,
            "total_queries": sum(self._query_counts.values()),
            "slow_query_count": len(self._slow_queries),
            "slow_query_threshold_ms": self.SLOW_QUERY_THRESHOLD_MS,
            "operations": [
                {
                    "name": s.name,
                    "count": s.count,
                    "avg_ms": round(s.avg, 2),
                    "p95_ms": round(s.p95, 2),
                    "max_ms": round(s.max, 2)
                }
                for s in summaries
            ],
            "recent_slow_queries": self._slow_queries[-10:]
        }


class HealthChecker:
    """
    Application health checking utility.

    Provides health status for:
    - Database connectivity
    - External services (Redis, S3)
    - Application metrics thresholds
    """

    def __init__(
        self,
        request_metrics: Optional[RequestMetrics] = None,
        db_metrics: Optional[DatabaseMetrics] = None
    ):
        self._request_metrics = request_metrics
        self._db_metrics = db_metrics
        self._custom_checks: Dict[str, Callable] = {}

    def register_check(self, name: str, check_fn: Callable) -> None:
        """
        Register a custom health check.

        Args:
            name: Check name
            check_fn: Function that returns (is_healthy: bool, message: str)
        """
        self._custom_checks[name] = check_fn

    async def check_health(self) -> Dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Health status dictionary
        """
        checks = {}
        overall_healthy = True

        # Run custom checks
        for name, check_fn in self._custom_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_fn):
                    is_healthy, message = await check_fn()
                else:
                    is_healthy, message = check_fn()
                checks[name] = {
                    "healthy": is_healthy,
                    "message": message
                }
                if not is_healthy:
                    overall_healthy = False
            except Exception as e:
                checks[name] = {
                    "healthy": False,
                    "message": f"Check failed: {str(e)}"
                }
                overall_healthy = False

        # Check request metrics thresholds
        if self._request_metrics:
            stats = self._request_metrics.get_all_stats(5)
            high_error_endpoints = [
                e for e in stats.get("endpoints", [])
                if e.get("error_rate", 0) > 5  # 5% error rate threshold
            ]

            checks["request_errors"] = {
                "healthy": len(high_error_endpoints) == 0,
                "message": f"{len(high_error_endpoints)} endpoints with high error rate" if high_error_endpoints else "All endpoints healthy"
            }

            if high_error_endpoints:
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }


# Global instances
metrics_collector = MetricsCollector()
request_metrics = RequestMetrics()
database_metrics = DatabaseMetrics()
health_checker = HealthChecker(request_metrics, database_metrics)


# Convenience functions
def timed(name: Optional[str] = None):
    """Decorator for timing function execution."""
    return metrics_collector.timed(name)


def record_metric(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Record a metric value."""
    metrics_collector.record(name, value, labels)


def get_metrics_report(window_minutes: int = 5) -> Dict[str, Any]:
    """Get comprehensive metrics report."""
    return {
        "collector": metrics_collector.to_dict(window_minutes),
        "requests": request_metrics.get_all_stats(window_minutes),
        "database": database_metrics.get_stats(window_minutes)
    }
