"""
Prometheus monitoring and metrics collection for XinShouCai.

This module provides:
- Request/response metrics (latency, count, errors)
- Business metrics (AI calls, risk events, etc.)
- Database connection pool metrics
- Custom application metrics
"""

import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

# Create a custom registry to avoid conflicts
REGISTRY = CollectorRegistry()

# ============================================================================
# Application Info
# ============================================================================

APP_INFO = Info(
    "xinshoucai_app",
    "Application information",
    registry=REGISTRY,
)

# ============================================================================
# HTTP Request Metrics
# ============================================================================

REQUEST_COUNT = Counter(
    "xinshoucai_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "xinshoucai_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=REGISTRY,
)

REQUEST_IN_PROGRESS = Gauge(
    "xinshoucai_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=REGISTRY,
)

# ============================================================================
# AI Engine Metrics
# ============================================================================

AI_REQUEST_COUNT = Counter(
    "xinshoucai_ai_requests_total",
    "Total AI API requests",
    ["engine_type", "status"],  # engine_type: patient_chat, doctor_chat, risk_detection
    registry=REGISTRY,
)

AI_REQUEST_LATENCY = Histogram(
    "xinshoucai_ai_request_duration_seconds",
    "AI API request latency in seconds",
    ["engine_type"],
    buckets=(0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0, 60.0),
    registry=REGISTRY,
)

AI_TOKENS_USED = Counter(
    "xinshoucai_ai_tokens_total",
    "Total AI tokens used",
    ["engine_type", "token_type"],  # token_type: input, output
    registry=REGISTRY,
)

# ============================================================================
# Risk Detection Metrics
# ============================================================================

RISK_EVENTS_DETECTED = Counter(
    "xinshoucai_risk_events_total",
    "Total risk events detected",
    ["level", "language"],  # level: CRITICAL, HIGH, MEDIUM, LOW
    registry=REGISTRY,
)

RISK_EVENTS_UNREVIEWED = Gauge(
    "xinshoucai_risk_events_unreviewed",
    "Number of unreviewed risk events",
    registry=REGISTRY,
)

# ============================================================================
# User Activity Metrics
# ============================================================================

ACTIVE_USERS = Gauge(
    "xinshoucai_active_users",
    "Number of active users",
    ["role"],  # role: patient, doctor, admin
    registry=REGISTRY,
)

USER_REGISTRATIONS = Counter(
    "xinshoucai_user_registrations_total",
    "Total user registrations",
    ["role"],
    registry=REGISTRY,
)

USER_LOGINS = Counter(
    "xinshoucai_user_logins_total",
    "Total user logins",
    ["role", "status"],  # status: success, failure
    registry=REGISTRY,
)

# ============================================================================
# Clinical Data Metrics
# ============================================================================

CHECKINS_SUBMITTED = Counter(
    "xinshoucai_checkins_total",
    "Total daily check-ins submitted",
    registry=REGISTRY,
)

ASSESSMENTS_COMPLETED = Counter(
    "xinshoucai_assessments_total",
    "Total assessments completed",
    ["assessment_type"],  # PHQ9, GAD7, PSS, ISI, PCL5
    registry=REGISTRY,
)

AVERAGE_MOOD_SCORE = Gauge(
    "xinshoucai_average_mood_score",
    "Average mood score across all patients (0-10)",
    registry=REGISTRY,
)

# ============================================================================
# Messaging Metrics
# ============================================================================

MESSAGES_SENT = Counter(
    "xinshoucai_messages_total",
    "Total messages sent",
    ["message_type"],  # text, image, file
    registry=REGISTRY,
)

WEBSOCKET_CONNECTIONS = Gauge(
    "xinshoucai_websocket_connections",
    "Number of active WebSocket connections",
    registry=REGISTRY,
)

# ============================================================================
# Database Metrics
# ============================================================================

DB_POOL_SIZE = Gauge(
    "xinshoucai_db_pool_size",
    "Database connection pool size",
    registry=REGISTRY,
)

DB_POOL_CHECKED_IN = Gauge(
    "xinshoucai_db_pool_checked_in",
    "Number of connections currently checked into the pool",
    registry=REGISTRY,
)

DB_POOL_CHECKED_OUT = Gauge(
    "xinshoucai_db_pool_checked_out",
    "Number of connections currently checked out of the pool",
    registry=REGISTRY,
)

DB_QUERY_LATENCY = Histogram(
    "xinshoucai_db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation"],  # select, insert, update, delete
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=REGISTRY,
)

# ============================================================================
# Email Metrics
# ============================================================================

EMAILS_SENT = Counter(
    "xinshoucai_emails_total",
    "Total emails sent",
    ["email_type", "status"],  # email_type: password_reset, risk_alert, appointment_reminder
    registry=REGISTRY,
)

EMAIL_QUEUE_SIZE = Gauge(
    "xinshoucai_email_queue_size",
    "Number of emails in queue",
    registry=REGISTRY,
)

# ============================================================================
# Storage Metrics
# ============================================================================

STORAGE_UPLOADS = Counter(
    "xinshoucai_storage_uploads_total",
    "Total file uploads",
    ["file_type"],  # image, document, report
    registry=REGISTRY,
)

STORAGE_UPLOAD_SIZE = Histogram(
    "xinshoucai_storage_upload_size_bytes",
    "Upload file size in bytes",
    buckets=(1024, 10240, 102400, 1048576, 10485760),  # 1KB, 10KB, 100KB, 1MB, 10MB
    registry=REGISTRY,
)

# ============================================================================
# Appointment Metrics
# ============================================================================

APPOINTMENTS_CREATED = Counter(
    "xinshoucai_appointments_total",
    "Total appointments created",
    ["status"],  # pending, confirmed, cancelled, completed
    registry=REGISTRY,
)

# ============================================================================
# Error Metrics
# ============================================================================

ERRORS_TOTAL = Counter(
    "xinshoucai_errors_total",
    "Total errors",
    ["error_type", "endpoint"],  # error_type: validation, auth, internal, external
    registry=REGISTRY,
)


# ============================================================================
# Helper Functions and Decorators
# ============================================================================


def init_app_info(version: str, environment: str) -> None:
    """Initialize application info metrics."""
    APP_INFO.info(
        {
            "version": version,
            "environment": environment,
            "name": "xinshoucai",
        }
    )


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST


@asynccontextmanager
async def track_request_latency(method: str, endpoint: str):
    """Context manager to track request latency."""
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


def track_ai_request(engine_type: str):
    """Decorator to track AI request metrics."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                AI_REQUEST_COUNT.labels(engine_type=engine_type, status="success").inc()
                return result
            except Exception as e:
                AI_REQUEST_COUNT.labels(engine_type=engine_type, status="error").inc()
                raise
            finally:
                duration = time.perf_counter() - start_time
                AI_REQUEST_LATENCY.labels(engine_type=engine_type).observe(duration)

        return wrapper

    return decorator


def track_db_query(operation: str):
    """Decorator to track database query metrics."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                DB_QUERY_LATENCY.labels(operation=operation).observe(duration)

        return wrapper

    return decorator


def record_request(method: str, endpoint: str, status_code: int) -> None:
    """Record an HTTP request."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()


def record_risk_event(level: str, language: str = "zh") -> None:
    """Record a detected risk event."""
    RISK_EVENTS_DETECTED.labels(level=level, language=language).inc()


def record_ai_tokens(engine_type: str, input_tokens: int, output_tokens: int) -> None:
    """Record AI token usage."""
    AI_TOKENS_USED.labels(engine_type=engine_type, token_type="input").inc(input_tokens)
    AI_TOKENS_USED.labels(engine_type=engine_type, token_type="output").inc(output_tokens)


def record_user_login(role: str, success: bool) -> None:
    """Record a user login attempt."""
    status = "success" if success else "failure"
    USER_LOGINS.labels(role=role, status=status).inc()


def record_user_registration(role: str) -> None:
    """Record a user registration."""
    USER_REGISTRATIONS.labels(role=role).inc()


def record_checkin() -> None:
    """Record a daily check-in submission."""
    CHECKINS_SUBMITTED.inc()


def record_assessment(assessment_type: str) -> None:
    """Record an assessment completion."""
    ASSESSMENTS_COMPLETED.labels(assessment_type=assessment_type).inc()


def record_message(message_type: str = "text") -> None:
    """Record a message sent."""
    MESSAGES_SENT.labels(message_type=message_type).inc()


def record_email(email_type: str, success: bool) -> None:
    """Record an email sent."""
    status = "success" if success else "failure"
    EMAILS_SENT.labels(email_type=email_type, status=status).inc()


def record_upload(file_type: str, size_bytes: int) -> None:
    """Record a file upload."""
    STORAGE_UPLOADS.labels(file_type=file_type).inc()
    STORAGE_UPLOAD_SIZE.observe(size_bytes)


def record_error(error_type: str, endpoint: str) -> None:
    """Record an error."""
    ERRORS_TOTAL.labels(error_type=error_type, endpoint=endpoint).inc()


def update_websocket_connections(count: int) -> None:
    """Update the number of active WebSocket connections."""
    WEBSOCKET_CONNECTIONS.set(count)


def update_unreviewed_risk_events(count: int) -> None:
    """Update the number of unreviewed risk events."""
    RISK_EVENTS_UNREVIEWED.set(count)


def update_email_queue_size(size: int) -> None:
    """Update the email queue size."""
    EMAIL_QUEUE_SIZE.set(size)


def update_db_pool_stats(pool_size: int, checked_in: int, checked_out: int) -> None:
    """Update database connection pool statistics."""
    DB_POOL_SIZE.set(pool_size)
    DB_POOL_CHECKED_IN.set(checked_in)
    DB_POOL_CHECKED_OUT.set(checked_out)


def update_active_users(role: str, count: int) -> None:
    """Update the number of active users."""
    ACTIVE_USERS.labels(role=role).set(count)


def update_average_mood(score: float) -> None:
    """Update the average mood score."""
    AVERAGE_MOOD_SCORE.set(score)
