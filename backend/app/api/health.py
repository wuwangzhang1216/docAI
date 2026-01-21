"""
Health check and monitoring endpoints for XinShouCai.

Provides:
- /health - Basic liveness check
- /health/ready - Readiness check (all dependencies)
- /health/live - Kubernetes liveness probe
- /metrics - Prometheus metrics endpoint
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.utils.monitoring import (
    get_metrics,
    get_metrics_content_type,
    update_db_pool_stats,
)

router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    environment: str


class DependencyHealth(BaseModel):
    """Individual dependency health status."""

    name: str
    status: str
    latency_ms: float | None = None
    error: str | None = None


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency details."""

    status: str
    timestamp: str
    version: str
    checks: list[DependencyHealth]


class DetailedHealthResponse(BaseModel):
    """Detailed health response with system information."""

    status: str
    timestamp: str
    version: str
    environment: str
    uptime_seconds: float
    checks: list[DependencyHealth]
    system: dict[str, Any]


# Track application start time
_start_time = datetime.now(timezone.utc)


async def check_database(db: AsyncSession) -> DependencyHealth:
    """Check database connectivity."""
    import time

    start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        return DependencyHealth(name="database", status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return DependencyHealth(
            name="database",
            status="unhealthy",
            latency_ms=round(latency, 2),
            error=str(e),
        )


async def check_redis() -> DependencyHealth:
    """Check Redis connectivity."""
    import time

    try:
        import redis.asyncio as redis

        start = time.perf_counter()
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        await client.close()
        latency = (time.perf_counter() - start) * 1000
        return DependencyHealth(name="redis", status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        return DependencyHealth(name="redis", status="unhealthy", error=str(e))


async def check_s3() -> DependencyHealth:
    """Check S3/MinIO connectivity."""
    import time

    try:
        import boto3
        from botocore.config import Config

        start = time.perf_counter()
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=5),
        )
        s3_client.head_bucket(Bucket=settings.S3_BUCKET)
        latency = (time.perf_counter() - start) * 1000
        return DependencyHealth(name="s3", status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        return DependencyHealth(name="s3", status="unhealthy", error=str(e))


@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Basic health check endpoint.

    Returns 200 OK if the application is running.
    Used for basic liveness checks.
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        environment="production" if not settings.DEBUG else "development",
    )


@router.get("/health/live", response_model=HealthStatus)
async def liveness_check() -> HealthStatus:
    """
    Kubernetes liveness probe endpoint.

    Returns 200 OK if the application process is alive.
    Does not check dependencies.
    """
    return HealthStatus(
        status="alive",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        environment="production" if not settings.DEBUG else "development",
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """
    Kubernetes readiness probe endpoint.

    Checks all critical dependencies:
    - Database connectivity
    - Redis connectivity
    - S3/MinIO connectivity

    Returns 200 OK only if all dependencies are healthy.
    """
    checks = [
        await check_database(db),
        await check_redis(),
        await check_s3(),
    ]

    all_healthy = all(check.status == "healthy" for check in checks)

    return ReadinessResponse(
        status="ready" if all_healthy else "not_ready",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        checks=checks,
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> DetailedHealthResponse:
    """
    Detailed health check with system information.

    Provides comprehensive health status including:
    - All dependency checks
    - System metrics
    - Uptime information
    """
    import os
    import platform

    checks = [
        await check_database(db),
        await check_redis(),
        await check_s3(),
    ]

    all_healthy = all(check.status == "healthy" for check in checks)
    uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()

    # Get system info
    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "pid": os.getpid(),
        "cpu_count": os.cpu_count(),
    }

    # Try to get memory info
    try:
        import psutil

        memory = psutil.virtual_memory()
        system_info["memory_total_mb"] = round(memory.total / (1024 * 1024), 2)
        system_info["memory_available_mb"] = round(memory.available / (1024 * 1024), 2)
        system_info["memory_percent"] = memory.percent
    except ImportError:
        pass

    return DetailedHealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        environment="production" if not settings.DEBUG else "development",
        uptime_seconds=round(uptime, 2),
        checks=checks,
        system=system_info,
    )


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint.

    Exposes application metrics in Prometheus format.
    """
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type(),
    )


@router.get("/health/db-pool")
async def database_pool_status(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Database connection pool status.

    Returns information about the SQLAlchemy connection pool.
    """
    from app.database import engine

    pool = engine.pool
    pool_status = {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, "invalidatedcount") else 0,
    }

    # Update Prometheus metrics
    update_db_pool_stats(
        pool_size=pool_status["pool_size"],
        checked_in=pool_status["checked_in"],
        checked_out=pool_status["checked_out"],
    )

    return pool_status
