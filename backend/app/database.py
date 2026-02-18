from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Build engine kwargs based on database backend
_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# Connection pool tuning for non-SQLite backends (SQLite uses NullPool by default)
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        {
            "pool_size": 10,  # Base number of persistent connections
            "max_overflow": 20,  # Extra connections under load
            "pool_timeout": 30,  # Seconds to wait for a connection
            "pool_recycle": 1800,  # Recycle connections after 30 min (avoid stale)
            "pool_pre_ping": True,  # Verify connections before use
        }
    )

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
