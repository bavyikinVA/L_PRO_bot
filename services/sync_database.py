from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, joinedload
from config import settings
from database.models import Booking

# Синхронный движок для Celery задач
sync_engine = create_engine(
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)


def get_booking_with_relations(booking_id: int):
    """Синхронная функция для получения брони с отношениями"""
    with SyncSessionLocal() as session:
        result = session.execute(
            select(Booking)
            .options(
                joinedload(Booking.specialist),
                joinedload(Booking.service),
                joinedload(Booking.user)
            )
            .where(booking_id == Booking.id)
        )
        return result.scalars().first()