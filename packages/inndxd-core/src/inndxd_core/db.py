# packages/inndxd-core/src/inndxd_core/db.py

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from inndxd_core.config import settings

uses_pool = not settings.database_url.startswith("sqlite")

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_size=20 if uses_pool else None,
    max_overflow=10 if uses_pool else None,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
