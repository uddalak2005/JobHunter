from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from core.config import settings

"""
Creates an asynchronous SQLAlchemy engine using the database URL from the settings.
"""
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

"""
Asynchronous SQLAlchemy engine for database connectivity.
The asynchronous equivalent of sessionmaker. It creates AsyncSession instances.
"""
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
