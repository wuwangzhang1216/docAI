"""
Structured logging configuration for XinShouCai.

This module provides:
- JSON structured logging for production
- Pretty console logging for development
- Request ID tracking
- User context in logs
- Performance timing
- Audit logging
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar("user_id", default=None)
user_role_var: ContextVar[Optional[str]] = ContextVar("user_role", default=None)


class StructuredLogFormatter(logging.Formatter):
    """JSON structured log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        user_role = user_role_var.get()
        if user_role:
            log_data["user_role"] = user_role

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class PrettyLogFormatter(logging.Formatter):
    """Pretty console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build prefix with context
        prefix_parts = [f"{color}{record.levelname:8}{self.RESET}"]

        request_id = request_id_var.get()
        if request_id:
            prefix_parts.append(f"[{request_id[:8]}]")

        user_id = user_id_var.get()
        if user_id:
            prefix_parts.append(f"[user:{user_id}]")

        prefix = " ".join(prefix_parts)

        # Format message
        message = record.getMessage()

        # Add extra data if present
        if hasattr(record, "extra_data") and record.extra_data:
            extra_str = " | " + " ".join(f"{k}={v}" for k, v in record.extra_data.items())
            message += extra_str

        output = f"{timestamp} {prefix} {record.name}: {message}"

        # Add exception if present
        if record.exc_info:
            output += "\n" + self.formatException(record.exc_info)

        return output


class ContextLogger(logging.Logger):
    """Custom logger that supports extra context data."""

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Any = None,
        extra: Optional[dict] = None,
        **kwargs,
    ) -> None:
        if extra is None:
            extra = {}

        # Extract extra_data from kwargs
        extra_data = kwargs.pop("extra_data", None)
        if extra_data:
            extra["extra_data"] = extra_data

        super()._log(level, msg, args, exc_info=exc_info, extra=extra, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(logging.DEBUG):
            self._log_with_extra(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(logging.INFO):
            self._log_with_extra(logging.INFO, msg, args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(logging.WARNING):
            self._log_with_extra(logging.WARNING, msg, args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(logging.ERROR):
            self._log_with_extra(logging.ERROR, msg, args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(logging.CRITICAL):
            self._log_with_extra(logging.CRITICAL, msg, args, **kwargs)


# Set our custom logger class
logging.setLoggerClass(ContextLogger)


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format (for production)
        log_file: Optional file path to write logs
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Choose formatter based on format type
    if json_format:
        formatter = StructuredLogFormatter()
    else:
        formatter = PrettyLogFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        # Always use JSON format for file logs
        file_handler.setFormatter(StructuredLogFormatter())
        root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> ContextLogger:
    """Get a logger instance with context support."""
    return logging.getLogger(name)  # type: ignore


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[int] = None,
    user_role: Optional[str] = None,
) -> str:
    """
    Set request context for logging.

    Returns:
        The request ID (generated if not provided)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    request_id_var.set(request_id)

    if user_id is not None:
        user_id_var.set(user_id)

    if user_role is not None:
        user_role_var.set(user_role)

    return request_id


def clear_request_context() -> None:
    """Clear request context after request completes."""
    request_id_var.set(None)
    user_id_var.set(None)
    user_role_var.set(None)


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return request_id_var.get()


# ============================================================================
# Logging Decorators
# ============================================================================


def log_execution_time(logger_name: Optional[str] = None):
    """Decorator to log function execution time."""

    def decorator(func: Callable) -> Callable:
        nonlocal logger_name
        if logger_name is None:
            logger_name = func.__module__

        log = get_logger(logger_name)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                log.info(
                    f"{func.__name__} completed",
                    extra_data={"duration_ms": round(duration_ms, 2)},
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                log.error(
                    f"{func.__name__} failed: {str(e)}",
                    extra_data={"duration_ms": round(duration_ms, 2)},
                    exc_info=True,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                log.info(
                    f"{func.__name__} completed",
                    extra_data={"duration_ms": round(duration_ms, 2)},
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                log.error(
                    f"{func.__name__} failed: {str(e)}",
                    extra_data={"duration_ms": round(duration_ms, 2)},
                    exc_info=True,
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============================================================================
# Audit Logging
# ============================================================================


class AuditLogger:
    """Logger for audit events that should be persisted."""

    def __init__(self):
        self.logger = get_logger("audit")

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        user_id: Optional[int] = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            action: The action performed (create, read, update, delete, login, etc.)
            resource_type: Type of resource (user, patient, conversation, etc.)
            resource_id: ID of the affected resource
            details: Additional details about the action
            user_id: ID of the user performing the action (uses context if not provided)
        """
        audit_data = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id or user_id_var.get(),
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_request_id(),
        }

        self.logger.info(
            f"AUDIT: {action} on {resource_type}",
            extra_data=audit_data,
        )

    def log_login(self, user_id: int, success: bool, ip_address: Optional[str] = None) -> None:
        """Log a login attempt."""
        self.log_action(
            action="login_success" if success else "login_failure",
            resource_type="auth",
            resource_id=user_id,
            details={"ip_address": ip_address},
            user_id=user_id,
        )

    def log_data_access(
        self,
        resource_type: str,
        resource_id: int,
        access_type: str = "read",
    ) -> None:
        """Log sensitive data access."""
        self.log_action(
            action=f"data_{access_type}",
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def log_data_export(self, user_id: int, export_type: str, data_types: list) -> None:
        """Log a data export request (GDPR)."""
        self.log_action(
            action="data_export",
            resource_type="gdpr",
            resource_id=user_id,
            details={"export_type": export_type, "data_types": data_types},
            user_id=user_id,
        )

    def log_risk_event(
        self,
        patient_id: int,
        risk_level: str,
        trigger_text: str,
        detected_by: str = "system",
    ) -> None:
        """Log a risk event detection."""
        self.log_action(
            action="risk_detected",
            resource_type="risk_event",
            resource_id=patient_id,
            details={
                "risk_level": risk_level,
                "trigger_text": trigger_text[:100],  # Truncate for privacy
                "detected_by": detected_by,
            },
        )


# Create global audit logger instance
audit_logger = AuditLogger()


# ============================================================================
# Request Logging Middleware Support
# ============================================================================


class RequestLogContext:
    """Context manager for request logging."""

    def __init__(
        self,
        method: str,
        path: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.method = method
        self.path = path
        self.client_ip = client_ip
        self.user_agent = user_agent
        self.start_time: float = 0
        self.request_id: str = ""
        self.logger = get_logger("request")

    def __enter__(self) -> "RequestLogContext":
        self.start_time = time.perf_counter()
        self.request_id = set_request_context()

        self.logger.info(
            f"Request started: {self.method} {self.path}",
            extra_data={
                "client_ip": self.client_ip,
                "user_agent": self.user_agent,
            },
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration_ms = (time.perf_counter() - self.start_time) * 1000

        if exc_type is not None:
            self.logger.error(
                f"Request failed: {self.method} {self.path}",
                extra_data={
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc_val),
                },
                exc_info=(exc_type, exc_val, exc_tb),
            )
        else:
            self.logger.info(
                f"Request completed: {self.method} {self.path}",
                extra_data={"duration_ms": round(duration_ms, 2)},
            )

        clear_request_context()


# ============================================================================
# Log Messages Constants
# ============================================================================


class LogMessages:
    """Standardized log messages for consistency."""

    # Auth
    AUTH_LOGIN_SUCCESS = "User logged in successfully"
    AUTH_LOGIN_FAILURE = "Login attempt failed"
    AUTH_LOGOUT = "User logged out"
    AUTH_TOKEN_REFRESH = "Token refreshed"
    AUTH_PASSWORD_RESET_REQUEST = "Password reset requested"
    AUTH_PASSWORD_RESET_COMPLETE = "Password reset completed"

    # AI
    AI_CHAT_START = "AI chat session started"
    AI_CHAT_RESPONSE = "AI response generated"
    AI_RISK_DETECTED = "Risk detected in user message"
    AI_CONTEXT_LOADED = "Patient context loaded for AI"

    # Clinical
    CLINICAL_CHECKIN_SUBMITTED = "Daily check-in submitted"
    CLINICAL_ASSESSMENT_COMPLETED = "Assessment completed"
    CLINICAL_NOTE_ADDED = "Clinical note added"

    # Messaging
    MESSAGE_SENT = "Message sent"
    WEBSOCKET_CONNECTED = "WebSocket connection established"
    WEBSOCKET_DISCONNECTED = "WebSocket connection closed"

    # Appointments
    APPOINTMENT_CREATED = "Appointment created"
    APPOINTMENT_CONFIRMED = "Appointment confirmed"
    APPOINTMENT_CANCELLED = "Appointment cancelled"

    # Data
    DATA_EXPORT_REQUESTED = "Data export requested"
    DATA_EXPORT_COMPLETED = "Data export completed"
    REPORT_GENERATED = "Report generated"

    # Errors
    ERROR_VALIDATION = "Validation error"
    ERROR_AUTH = "Authentication error"
    ERROR_PERMISSION = "Permission denied"
    ERROR_NOT_FOUND = "Resource not found"
    ERROR_INTERNAL = "Internal server error"
    ERROR_EXTERNAL = "External service error"
