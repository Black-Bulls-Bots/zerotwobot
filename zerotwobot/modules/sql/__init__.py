import asyncio
from zerotwobot import DB_URI
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_scoped_session, async_sessionmaker

async def start_db() -> async_scoped_session:
    engine = create_async_engine(DB_URI, client_encoding="utf8", echo=True)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return async_scoped_session(async_sessionmaker(bind=engine, autoflush=False))


class BASE(DeclarativeBase):
    pass

SESSION = asyncio.get_event_loop().run_until_complete(start_db())