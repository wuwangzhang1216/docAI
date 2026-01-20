"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.websocket import router as websocket_router
from app.config import settings
from app.database import init_db
from app.utils.rate_limit import RateLimitMiddleware, cleanup_rate_limiters


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME}...")

    # Initialize database tables (for development)
    if settings.DEBUG:
        await init_db()
        print("Database tables initialized")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")

    # Cleanup rate limiters
    await cleanup_rate_limiters()


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

# Add rate limiting middleware (order matters - runs after CORS)
app.add_middleware(RateLimitMiddleware)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include WebSocket routes (no prefix, direct at /ws)
app.include_router(websocket_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": settings.APP_NAME, "version": "0.1.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
