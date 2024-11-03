from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import ErrorHandler
from app.core.database import async_session_maker
from sqlalchemy import select, insert
from pydantic import UUID4

class BaseDao(ErrorHandler):
    # Модель базы данных, с которой будет работать DAO (Data Access Object).
    model = None
    # Часть сообщения, которое будет возвращено при ошибках в базе данных.
    _type_error_message = "Database Error"
    # Тип исключения, который будет использоваться для обработки ошибок.
    _type_error = SQLAlchemyError

    @classmethod
    async def add(cls, **data):
        """
        Добавляет новый объект в базу данных.
        :param data: Данные для создания нового объекта.
        :return: Сохранённый объект, если успешно, иначе None.
        """
        try:
            # Создание асинхронной сессии
            async with async_session_maker() as session:
                # Формирование запроса для добавления новой записи
                query = (
                    insert(cls.model)
                    .values(**data)
                    .returning(*cls.model.__table__.columns)  # Возвращаем все колонки объекта
                )
                # Выполнение запроса
                result = await session.execute(query)
                # Подтверждение транзакции
                await session.commit()
                # Возвращение созданного объекта
                return result.fetchone()
        except (SQLAlchemyError, Exception) as e:
            # Логирование ошибки с деталями
            cls._log_error(
                e,
                error_message=f"Cannot add new {cls.model.__name__}",
                extra=data
            )

    @classmethod
    async def find_by_id(cls, model_id: int | UUID4):
        """
        Находит объект по его ID.
        :param model_id: Идентификатор объекта.
        :return: Найденный объект или None, если объект не найден.
        """
        try:
            # Создание асинхронной сессии
            async with async_session_maker() as session:
                # Формирование запроса для поиска объекта по ID
                query = select(cls.model).filter_by(id=model_id)
                # Выполнение запроса
                result = await session.execute(query)
                # Возвращение найденного объекта или None
                return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as e:
            # Логирование ошибки с деталями
            cls._log_error(
                e,
                error_message=f"Cannot find {cls.model.__name__} by id",
                extra={
                    "model_id": model_id
                }
            )

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        """
        Находит один объект, соответствующий заданным фильтрам.
        :param filter_by: Критерии фильтрации.
        :return: Найденный объект или None, если объект не найден.
        """
        try:
            # Создание асинхронной сессии
            async with async_session_maker() as session:
                # Формирование запроса для поиска объекта с фильтрацией
                query = select(cls.model).filter_by(**filter_by)
                # Выполнение запроса
                result = await session.execute(query)
                # Возвращение найденного объекта или None
                return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as e:
            # Логирование ошибки с деталями
            cls._log_error(
                e,
                error_message=f"Cannot find one or none for model {cls.model.__name__}",
                extra=filter_by
            )

    @classmethod
    async def find_all(cls):
        """
        Находит все объекты данного типа в базе данных.
        :return: Список всех объектов.
        """
        try:
            # Создание асинхронной сессии
            async with async_session_maker() as session:
                # Формирование запроса для поиска всех объектов
                query = select(cls.model)
                # Выполнение запроса
                result = await session.execute(query)
                # Возвращение всех найденных объектов в виде списка
                return result.scalars().all()
        except (SQLAlchemyError, Exception) as e:
            # Логирование ошибки с деталями
            cls._log_error(
                e,
                error_message=f"Cannot find all for model {cls.model.__name__}"
            )
