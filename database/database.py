from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from config import settings
from typing import AsyncGenerator


# асинхронный движок с пулом соединений
engine = create_async_engine(
    url=settings.get_db_url(),
    pool_size=20,      # стандартные соединения
    max_overflow=10,   # дополнительные при пиковой нагрузке
    pool_pre_ping=True # проверка активности соединения перед использованием
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True


class DatabaseSession:
    @staticmethod
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session


    @staticmethod
    async def get_db_with_commit() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


db = DatabaseSession()