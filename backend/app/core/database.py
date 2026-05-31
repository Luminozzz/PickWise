import ssl

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.config import DATABASE_URL, DB_SCHEMA

connect_args = {}
engine_kwargs = dict(echo=False)

if DATABASE_URL.startswith("postgresql"):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args = {
        "ssl": ssl_ctx,
        # ensure unqualified table names resolve to our schema on every connection
        "server_settings": {"search_path": DB_SCHEMA},
    }
    engine_kwargs["poolclass"] = NullPool
else:
    # SQLite fallback
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
