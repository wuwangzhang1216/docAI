"""
Unit tests for metrics and monitoring utilities.

Tests cover:
- MetricsCollector for recording and summarizing metrics
- RequestMetrics for HTTP request tracking
- DatabaseMetrics for query tracking
- HealthChecker for health status
- Timer context manager and decorator
"""

import time
import asyncio
from datetime import datetime, timedelta

import pytest

from app.utils.metrics import (
    MetricsCollector,
    MetricPoint,
    MetricSummary,
    RequestMetrics,
    DatabaseMetrics,
    HealthChecker,
    metrics_collector,
    request_metrics,
    database_metrics,
    timed,
    record_metric,
    get_metrics_report,
)


# ============================================
# MetricsCollector Tests
# ============================================

class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_record_metric(self):
        """Test recording a simple metric."""
        collector = MetricsCollector()
        collector.record("test_metric", 100.5)

        summary = collector.get_summary("test_metric")
        assert summary is not None
        assert summary.count == 1
        assert summary.avg == 100.5

    def test_record_multiple_metrics(self):
        """Test recording multiple metric values."""
        collector = MetricsCollector()
        values = [10, 20, 30, 40, 50]

        for v in values:
            collector.record("multi_metric", v)

        summary = collector.get_summary("multi_metric")
        assert summary.count == 5
        assert summary.total == 150
        assert summary.avg == 30
        assert summary.min == 10
        assert summary.max == 50

    def test_record_with_labels(self):
        """Test recording metrics with labels."""
        collector = MetricsCollector()
        collector.record("labeled_metric", 100, labels={"endpoint": "/api/v1/test", "method": "GET"})

        summary = collector.get_summary("labeled_metric")
        assert summary is not None
        assert summary.count == 1

    def test_record_error(self):
        """Test recording errors."""
        collector = MetricsCollector()
        collector.record("error_metric", 50)
        collector.record_error("error_metric")
        collector.record_error("error_metric")

        summary = collector.get_summary("error_metric")
        assert summary.error_count == 2
        assert summary.error_rate == 2.0  # 2 errors / 1 record

    def test_get_summary_no_data(self):
        """Test getting summary for non-existent metric."""
        collector = MetricsCollector()
        summary = collector.get_summary("nonexistent")
        assert summary is None

    def test_get_summary_window(self):
        """Test summary respects time window."""
        collector = MetricsCollector()
        collector.record("window_metric", 100)

        # Get summary for last 5 minutes
        summary = collector.get_summary("window_metric", window_minutes=5)
        assert summary is not None
        assert summary.count == 1

    def test_get_all_summaries(self):
        """Test getting summaries for all metrics."""
        collector = MetricsCollector()
        collector.record("metric_a", 10)
        collector.record("metric_b", 20)
        collector.record("metric_c", 30)

        summaries = collector.get_all_summaries()
        assert len(summaries) == 3

        names = [s.name for s in summaries]
        assert "metric_a" in names
        assert "metric_b" in names
        assert "metric_c" in names

    def test_percentile_calculations(self):
        """Test percentile calculations."""
        collector = MetricsCollector()

        # Record 100 values from 1 to 100
        for i in range(1, 101):
            collector.record("percentile_metric", i)

        summary = collector.get_summary("percentile_metric")
        assert summary.count == 100
        # Percentile values depend on implementation (index-based)
        assert 49 <= summary.p50 <= 51  # Around median
        assert 94 <= summary.p95 <= 96  # Around 95th percentile
        assert 98 <= summary.p99 <= 100  # Around 99th percentile

    def test_max_history_limit(self):
        """Test that metrics respect max history limit."""
        collector = MetricsCollector(max_history=10)

        # Record more than max history
        for i in range(20):
            collector.record("limited_metric", i)

        # Should only keep last 10
        summary = collector.get_summary("limited_metric")
        assert summary.count <= 10

    def test_timer_context_manager(self):
        """Test timer context manager."""
        collector = MetricsCollector()

        with collector.timer("timed_operation"):
            time.sleep(0.01)  # 10ms

        summary = collector.get_summary("timed_operation")
        assert summary is not None
        assert summary.count == 1
        assert summary.avg >= 10  # At least 10ms

    def test_timer_records_error(self):
        """Test timer records errors on exception."""
        collector = MetricsCollector()

        with pytest.raises(ValueError):
            with collector.timer("error_timer"):
                raise ValueError("Test error")

        summary = collector.get_summary("error_timer")
        assert summary.error_count == 1

    def test_timed_decorator_sync(self):
        """Test timed decorator for sync functions."""
        collector = MetricsCollector()

        @collector.timed("sync_function")
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"

        summary = collector.get_summary("sync_function")
        assert summary is not None
        assert summary.avg >= 10

    @pytest.mark.asyncio
    async def test_timed_decorator_async(self):
        """Test timed decorator for async functions."""
        collector = MetricsCollector()

        @collector.timed("async_function")
        async def async_slow_function():
            await asyncio.sleep(0.01)
            return "async done"

        result = await async_slow_function()
        assert result == "async done"

        summary = collector.get_summary("async_function")
        assert summary is not None
        assert summary.avg >= 10

    def test_timed_decorator_error(self):
        """Test timed decorator records errors."""
        collector = MetricsCollector()

        @collector.timed("error_function")
        def error_function():
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError):
            error_function()

        summary = collector.get_summary("error_function")
        assert summary.error_count == 1

    def test_get_uptime(self):
        """Test uptime calculation."""
        collector = MetricsCollector()
        uptime = collector.get_uptime()

        assert isinstance(uptime, timedelta)
        assert uptime.total_seconds() >= 0

    def test_reset(self):
        """Test reset clears all metrics."""
        collector = MetricsCollector()
        collector.record("test", 100)
        collector.record_error("test")

        collector.reset()

        assert collector.get_summary("test") is None
        summaries = collector.get_all_summaries()
        assert len(summaries) == 0

    def test_to_dict(self):
        """Test exporting metrics to dictionary."""
        collector = MetricsCollector()
        collector.record("export_metric", 100)

        result = collector.to_dict()

        assert "uptime_seconds" in result
        assert "window_minutes" in result
        assert "metrics" in result
        assert len(result["metrics"]) == 1
        assert result["metrics"][0]["name"] == "export_metric"


# ============================================
# RequestMetrics Tests
# ============================================

class TestRequestMetrics:
    """Tests for RequestMetrics class."""

    def test_record_request(self):
        """Test recording an HTTP request."""
        metrics = RequestMetrics()
        metrics.record_request(
            endpoint="/api/v1/test",
            method="GET",
            status_code=200,
            duration_ms=50.5
        )

        stats = metrics.get_endpoint_stats("/api/v1/test", "GET")
        assert stats is not None
        assert stats["total_requests"] == 1
        assert stats["avg_response_time_ms"] == 50.5

    def test_record_multiple_requests(self):
        """Test recording multiple requests."""
        metrics = RequestMetrics()

        for i in range(10):
            metrics.record_request(
                endpoint="/api/v1/users",
                method="GET",
                status_code=200,
                duration_ms=100 + i * 10
            )

        stats = metrics.get_endpoint_stats("/api/v1/users", "GET")
        assert stats["total_requests"] == 10

    def test_record_error_request(self):
        """Test error requests are tracked."""
        metrics = RequestMetrics()
        metrics.record_request("/api/v1/fail", "POST", 500, 100)
        metrics.record_request("/api/v1/fail", "POST", 200, 50)

        stats = metrics.get_endpoint_stats("/api/v1/fail", "POST")
        assert stats["error_rate"] == 50.0  # 1 error out of 2

    def test_status_code_distribution(self):
        """Test status code distribution tracking."""
        metrics = RequestMetrics()
        metrics.record_request("/api/v1/mixed", "GET", 200, 50)
        metrics.record_request("/api/v1/mixed", "GET", 200, 50)
        metrics.record_request("/api/v1/mixed", "GET", 404, 30)
        metrics.record_request("/api/v1/mixed", "GET", 500, 100)

        stats = metrics.get_endpoint_stats("/api/v1/mixed", "GET")
        assert stats["status_codes"][200] == 2
        assert stats["status_codes"][404] == 1
        assert stats["status_codes"][500] == 1

    def test_get_all_stats(self):
        """Test getting stats for all endpoints."""
        metrics = RequestMetrics()
        metrics.record_request("/api/v1/a", "GET", 200, 50)
        metrics.record_request("/api/v1/b", "POST", 201, 100)
        metrics.record_request("/api/v1/c", "DELETE", 204, 75)

        stats = metrics.get_all_stats()
        assert stats["total_requests"] == 3
        assert len(stats["endpoints"]) == 3

    def test_endpoints_sorted_by_requests(self):
        """Test endpoints are sorted by request count."""
        metrics = RequestMetrics()

        # Record different amounts for different endpoints
        for _ in range(5):
            metrics.record_request("/api/v1/popular", "GET", 200, 50)
        for _ in range(2):
            metrics.record_request("/api/v1/less", "GET", 200, 50)

        stats = metrics.get_all_stats()
        assert stats["endpoints"][0]["endpoint"] == "/api/v1/popular"

    def test_get_nonexistent_endpoint(self):
        """Test getting stats for nonexistent endpoint."""
        metrics = RequestMetrics()
        stats = metrics.get_endpoint_stats("/api/v1/nonexistent", "GET")
        assert stats is None


# ============================================
# DatabaseMetrics Tests
# ============================================

class TestDatabaseMetrics:
    """Tests for DatabaseMetrics class."""

    def test_record_query(self):
        """Test recording a database query."""
        metrics = DatabaseMetrics()
        metrics.record_query("SELECT", "users", 25.5, rows_affected=10)

        stats = metrics.get_stats()
        assert stats["total_queries"] == 1

    def test_slow_query_detection(self):
        """Test slow query detection."""
        metrics = DatabaseMetrics()

        # Fast query
        metrics.record_query("SELECT", "users", 50)

        # Slow query (over 100ms threshold)
        metrics.record_query("SELECT", "large_table", 150, rows_affected=1000)

        stats = metrics.get_stats()
        assert stats["slow_query_count"] == 1
        assert len(stats["recent_slow_queries"]) == 1
        assert stats["recent_slow_queries"][0]["table"] == "large_table"

    def test_slow_query_limit(self):
        """Test slow queries are limited to 100."""
        metrics = DatabaseMetrics()

        # Record 150 slow queries
        for i in range(150):
            metrics.record_query("SELECT", f"table_{i}", 200)

        stats = metrics.get_stats()
        # Should only keep last 100
        assert len(metrics._slow_queries) <= 100

    def test_multiple_operations(self):
        """Test tracking different operation types."""
        metrics = DatabaseMetrics()
        metrics.record_query("SELECT", "users", 20)
        metrics.record_query("INSERT", "users", 30)
        metrics.record_query("UPDATE", "users", 40)
        metrics.record_query("DELETE", "users", 25)

        stats = metrics.get_stats()
        assert stats["total_queries"] == 4
        assert len(stats["operations"]) == 4

    def test_stats_format(self):
        """Test stats output format."""
        metrics = DatabaseMetrics()
        metrics.record_query("SELECT", "users", 50)

        stats = metrics.get_stats()
        assert "window_minutes" in stats
        assert "total_queries" in stats
        assert "slow_query_count" in stats
        assert "slow_query_threshold_ms" in stats
        assert "operations" in stats
        assert "recent_slow_queries" in stats


# ============================================
# HealthChecker Tests
# ============================================

class TestHealthChecker:
    """Tests for HealthChecker class."""

    @pytest.mark.asyncio
    async def test_healthy_status(self):
        """Test healthy status with no issues."""
        checker = HealthChecker()

        # Register a healthy check
        checker.register_check("test_check", lambda: (True, "All good"))

        result = await checker.check_health()
        assert result["status"] == "healthy"
        assert result["checks"]["test_check"]["healthy"] is True

    @pytest.mark.asyncio
    async def test_unhealthy_status(self):
        """Test unhealthy status with failing check."""
        checker = HealthChecker()

        # Register an unhealthy check
        checker.register_check("failing_check", lambda: (False, "Database connection failed"))

        result = await checker.check_health()
        assert result["status"] == "unhealthy"
        assert result["checks"]["failing_check"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_async_check(self):
        """Test async health check function."""
        checker = HealthChecker()

        async def async_check():
            await asyncio.sleep(0.001)
            return True, "Async check passed"

        checker.register_check("async_check", async_check)

        result = await checker.check_health()
        assert result["checks"]["async_check"]["healthy"] is True

    @pytest.mark.asyncio
    async def test_check_exception_handling(self):
        """Test health check handles exceptions."""
        checker = HealthChecker()

        def failing_check():
            raise RuntimeError("Check crashed")

        checker.register_check("crash_check", failing_check)

        result = await checker.check_health()
        assert result["status"] == "unhealthy"
        assert result["checks"]["crash_check"]["healthy"] is False
        assert "Check failed" in result["checks"]["crash_check"]["message"]

    @pytest.mark.asyncio
    async def test_high_error_rate_detection(self):
        """Test detection of high error rate endpoints."""
        req_metrics = RequestMetrics()
        checker = HealthChecker(request_metrics=req_metrics)

        # Record requests with high error rate
        for _ in range(10):
            req_metrics.record_request("/api/v1/bad", "GET", 500, 100)

        result = await checker.check_health()
        assert result["checks"]["request_errors"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_result_format(self):
        """Test health check result format."""
        checker = HealthChecker()

        result = await checker.check_health()
        assert "status" in result
        assert "timestamp" in result
        assert "checks" in result


# ============================================
# Global Functions Tests
# ============================================

class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_record_metric_function(self):
        """Test global record_metric function."""
        # Reset collector
        metrics_collector.reset()

        record_metric("global_test", 42)

        summary = metrics_collector.get_summary("global_test")
        assert summary is not None
        assert summary.avg == 42

    def test_timed_decorator(self):
        """Test global timed decorator."""
        metrics_collector.reset()

        @timed("global_timed_func")
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"

        summary = metrics_collector.get_summary("global_timed_func")
        assert summary is not None

    def test_get_metrics_report(self):
        """Test comprehensive metrics report."""
        metrics_collector.reset()
        record_metric("report_test", 100)

        report = get_metrics_report()

        assert "collector" in report
        assert "requests" in report
        assert "database" in report


# ============================================
# MetricPoint and MetricSummary Tests
# ============================================

class TestDataClasses:
    """Tests for metric data classes."""

    def test_metric_point_creation(self):
        """Test MetricPoint creation."""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=100.5,
            labels={"key": "value"}
        )

        assert point.value == 100.5
        assert point.labels == {"key": "value"}

    def test_metric_point_default_labels(self):
        """Test MetricPoint default labels."""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=50
        )

        assert point.labels == {}

    def test_metric_summary_creation(self):
        """Test MetricSummary creation."""
        summary = MetricSummary(
            name="test",
            count=100,
            total=5000,
            min=10,
            max=100,
            avg=50,
            p50=50,
            p95=95,
            p99=99,
            error_count=5,
            error_rate=0.05
        )

        assert summary.name == "test"
        assert summary.count == 100
        assert summary.error_rate == 0.05
