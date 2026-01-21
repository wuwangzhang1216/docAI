"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.health import router as health_router
from app.api.websocket import router as websocket_router
from app.config import settings
from app.database import init_db
from app.middleware.observability import ObservabilityMiddleware
from app.utils.logging_config import get_logger, setup_logging
from app.utils.monitoring import init_app_info
from app.utils.rate_limit import RateLimitMiddleware, cleanup_rate_limiters

# Setup structured logging
setup_logging(
    level="DEBUG" if settings.DEBUG else "INFO",
    json_format=not settings.DEBUG,  # JSON format for production
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...", extra_data={"version": "0.1.0"})

    # Initialize Prometheus metrics
    init_app_info(
        version="0.1.0",
        environment="development" if settings.DEBUG else "production",
    )

    # Initialize database tables (for development)
    if settings.DEBUG:
        await init_db()
        logger.info("Database tables initialized")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")

    # Cleanup rate limiters
    await cleanup_rate_limiters()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="心理健康支持平台后端服务",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Next.js dev server (alternate port)
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add observability middleware (metrics, logging, request tracking)
app.add_middleware(ObservabilityMiddleware)

# Add rate limiting middleware (order matters - runs after CORS)
app.add_middleware(RateLimitMiddleware)

# Include health check and metrics routes (no auth required)
app.include_router(health_router)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include WebSocket routes (no prefix, direct at /ws)
app.include_router(websocket_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": settings.APP_NAME, "version": "0.1.0", "status": "running"}
