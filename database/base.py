from typing import List, TypeVar, Generic, Dict, Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func, update
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from database.database import Base


# типовой параметр T, наследник Base
T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    model: type[T]


    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession):
        logger.info(f"Поиск {cls.model.__name__} с ID: {data_id}")
        try:
            query = select(cls.model).filter_by(id=data_id).execution_options(populate_existing=True)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись с ID {data_id} найдена.")
            else:
                logger.info(f"Запись с ID {data_id} не найдена.")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи с ID {data_id}: {e}")
            raise


    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        # Найти одну запись по фильтрам
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Поиск одной записи {cls.model.__name__} по фильтрам: {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict).execution_options(populate_existing=True)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись найдена по фильтрам: {filter_dict}")
            else:
                logger.info(f"Запись не найдена по фильтрам: {filter_dict}")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи по фильтрам {filter_dict}: {e}")
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None = None):
        # Найти все записи по фильтрам
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f"Поиск всех записей {cls.model.__name__} по фильтрам: {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            records = result.scalars().all()
            logger.info(f"Найдено {len(records)} записей.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске всех записей по фильтрам {filter_dict}: {e}")
            raise


    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel, commit: bool = True) -> T:
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Добавление записи {cls.model.__name__} с параметрами: {values_dict}")
        try:
            new_instance = cls.model(**values_dict)
            session.add(new_instance)
            await session.flush()
            if commit:
                await session.commit()
                await session.refresh(new_instance)
            logger.info(f"Запись {cls.model.__name__} успешно добавлена и сделан commit.")
            return new_instance
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении записи: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при добавлении записи: {str(e)}")


    @classmethod
    async def add_many(cls, session: AsyncSession, instances: List[BaseModel], commit: bool = True):
        values_list = [item.model_dump(exclude_unset=True) for item in instances]
        logger.info(f"Добавление нескольких записей {cls.model.__name__}. Количество: {len(values_list)}")
        new_instances = [cls.model(**values) for values in values_list]
        session.add_all(new_instances)
        try:
            if commit:
                await session.commit()
                for instance in new_instances:
                    await session.refresh(instance)
            logger.info(f"Успешно добавлено {len(new_instances)} записей.")
            return new_instances
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении нескольких записей: {e}")
            raise e

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            filters: Dict[str, Any] | List[InstrumentedAttribute],
            values: Dict[str, Any],
            commit: bool = True,
            load_options: Optional[List[Any]] = None
    ) -> Optional[T]:
        if not values:
            raise ValueError("Нет данных для обновления")

        # формируем условия фильтрации
        if isinstance(filters, dict):
            where_conditions = [getattr(cls.model, k) == v for k, v in filters.items()]
        else:
            where_conditions = filters

        # обновляем запись
        stmt = update(cls.model).where(*where_conditions).values(**values)
        try:
            result = await session.execute(stmt)
            if result.rowcount == 0:
                logger.info(f"Обновление не выполнено: запись не найдена для фильтров {filters}")
                return None

            if commit:
                await session.commit()

            # возвращаем обновлённый объект
            query = select(cls.model).where(*where_conditions)
            if load_options:
                query = query.options(*load_options)
            result = await session.execute(query)
            instance = result.scalars().first()
            return instance
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при обновлении записи: {str(e)}")
            raise


    @classmethod
    async def delete(cls, session: AsyncSession, filters: BaseModel, commit: bool = True):
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Удаление записей {cls.model.__name__} по фильтру: {filter_dict}")
        if not filter_dict:
            logger.error("Нужен хотя бы один фильтр для удаления.")
            raise ValueError("Нужен хотя бы один фильтр для удаления.")

        query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
        try:
            result = await session.execute(query)
            if commit:
                await session.flush()
            logger.info(f"Удалено {result.rowcount} записей.")
            return result.rowcount
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при удалении записей: {e}")
            raise e


    @classmethod
    async def count(cls, session: AsyncSession, filters: BaseModel | None = None) -> int:
        # подсчет количества записей
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f"Подсчет количества записей {cls.model.__name__} по фильтру: {filter_dict}")
        try:
            query = select(func.count(cls.model.id)).filter_by(**filter_dict)
            result = await session.execute(query)
            count = result.scalar()
            logger.info(f"Найдено {count} записей.")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при подсчете записей: {e}")
            raise


    @classmethod
    async def paginate(cls, session: AsyncSession, page: int = 1, page_size: int = 10, filters: BaseModel = None):
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(
            f"Пагинация записей {cls.model.__name__} по фильтру: {filter_dict}, страница: {page}, размер страницы: {page_size}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
            records = result.scalars().all()
            logger.info(f"Найдено {len(records)} записей на странице {page}.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при пагинации записей: {e}")
            raise


    @classmethod
    async def find_by_ids(cls, session: AsyncSession, ids: List[int]):
        logger.info(f"Поиск записей {cls.model.__name__} по списку ID: {ids}")
        try:
            query = select(cls.model).filter(cls.model.id.in_(ids)).execution_options(populate_existing=True)
            result = await session.execute(query)
            records = result.scalars().all()
            logger.info(f"Найдено {len(records)} записей по списку ID.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записей по списку ID: {e}")
            raise


    @classmethod
    async def upsert(cls, session: AsyncSession, unique_fields: List[str], values: BaseModel, commit: bool = True):
        """Создать запись или обновить существующую"""
        values_dict = values.model_dump(exclude_unset=True)
        filter_dict = {field: values_dict[field] for field in unique_fields if field in values_dict}

        logger.info(f"Upsert для {cls.model.__name__}")
        try:
            existing = await cls.find_one_or_none(session, BaseModel.construct(**filter_dict))
            if existing:
                # Обновляем существующую запись
                for key, value in values_dict.items():
                    setattr(existing, key, value)
                if commit:
                    await session.commit()
                logger.info(f"Обновлена существующая запись {cls.model.__name__}")
                return existing
            else:
                # Создаем новую запись
                new_instance = cls.model(**values_dict)
                session.add(new_instance)
                if commit:
                    await session.commit()
                    await session.refresh(new_instance)
                logger.info(f"Создана новая запись {cls.model.__name__}")
                return new_instance
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при upsert: {e}")
            raise


    @classmethod
    async def bulk_update(cls, session: AsyncSession, records: List[BaseModel], commit: bool = True) -> int:
        """Массовое обновление записей"""
        logger.info(f"Массовое обновление записей {cls.model.__name__}")
        try:
            updated_count = 0
            for record in records:
                record_dict = record.model_dump(exclude_unset=True)
                if 'id' not in record_dict:
                    continue

                update_data = {k: v for k, v in record_dict.items() if k != 'id'}
                stmt = (
                    sqlalchemy_update(cls.model)
                    .filter_by(id=record_dict['id'])
                    .values(**update_data)
                )
                result = await session.execute(stmt)
                updated_count += result.rowcount
            if commit:
                await session.commit()
            logger.info(f"Обновлено {updated_count} записей")
            return updated_count
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при массовом обновлении: {e}")
            raise