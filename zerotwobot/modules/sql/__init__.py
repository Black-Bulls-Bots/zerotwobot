import asyncio
from zerotwobot import DB_URI
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_scoped_session,
    async_sessionmaker,
)


async def start_db() -> async_scoped_session:
    engine = create_async_engine(DB_URI, echo=True)
    BASE.metadata.bind = engine
    async with engine.begin() as conn:
        await conn.run_sync(BASE.metadata.create_all)
    return async_scoped_session(
        async_sessionmaker(bind=engine, autoflush=False), asyncio.current_task()
    )


class BASE(DeclarativeBase):
    pass


SESSION = asyncio.get_event_loop().run_until_complete(start_db())
