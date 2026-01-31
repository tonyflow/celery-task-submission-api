from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine("postgresql+asyncpg://postgres:postgres@postgres:5432/postgres")
"""Database engine for async operations"""

async_session = async_sessionmaker(engine)
"""Database session for async operations"""