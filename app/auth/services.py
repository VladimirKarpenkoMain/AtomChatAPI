from pydantic import UUID4

from app.auth.auth_utilits import (
    authentication,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    refresh,
)
from app.auth.dao import BlockDao, UsersDao
from app.auth.shemas import SRefreshToken, STokenInfo, SUserAuth, SUserRegister
from app.core.exceptions import (
    IncorrectEmailOrPasswordException,
    PasswordsDoesNotMatchException,
    UserEmailExistsException,
    UserIsAlreadyBlockedException,
    UserUsernameExistsException,
)


class AuthService:
    @classmethod
    async def register_user(cls, user_data: SUserRegister):
        """
        Регистрирует нового пользователя в системе, проверяя наличие email и username в БД.
        :param user_data: Данные пользователя для регистрации (email, username, password).
        :raises UserEmailExistsException: Если email уже используется.
        :raises UserUsernameExistsException: Если username уже используется.
        :raises PasswordsDoesNotMatchException: Если пароль и его повторение не совпадают.
        :return: Словарь с информацией об успешной регистрации.
        """
        # Проверка на наличие пользователя с таким же email или username
        existing_user = await UsersDao.find_by_email_or_username(
            email=user_data.email, username=user_data.username
        )
        if existing_user:
            if existing_user.email == user_data.email:
                raise UserEmailExistsException
            if existing_user.username == user_data.username:
                raise UserUsernameExistsException

        # Проверка совпадения паролей
        if user_data.password != user_data.password_repiet:
            raise PasswordsDoesNotMatchException

        # Хеширование пароля и добавление пользователя в БД
        hashed_password = get_password_hash(user_data.password)
        await UsersDao.add(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        return {"detail": "The user has been registered successfully."}

    @classmethod
    async def jwt_login_user(cls, user_data: SUserAuth) -> STokenInfo:
        """
        Авторизует пользователя и выдает JWT access и refresh токены.
        :param user_data: Данные пользователя для авторизации (email, password).
        :raises IncorrectEmailOrPasswordException: Если email или пароль неверны.
        :return: Объект с access и refresh токенами.
        """
        # Аутентификация пользователя
        user = await authentication(user_data.email, user_data.password)
        if user is None:
            raise IncorrectEmailOrPasswordException

        # Генерация access и refresh токенов
        access_token: str = create_access_token(user)
        refresh_token: str = create_refresh_token(user)

        # Обновление refresh токена в БД
        await UsersDao.update_refresh_token(user_id=user.id, token=refresh_token)

        return STokenInfo(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @classmethod
    async def jwt_refresh_token(cls, refresh_token_data: SRefreshToken) -> STokenInfo:
        """
        Обновляет access и refresh токены, используя refresh токен.
        :param refresh_token_data: Объект с данными refresh токена.
        :return: Обновленный объект с access и refresh токенами.
        """
        # Обновление токенов на основе переданного refresh токена
        result = await refresh(refresh_token=refresh_token_data.refresh_token)
        return result


class BlockService:
    @classmethod
    async def block_user(cls, user_id: UUID4, moderator_id: UUID4, reason: str):
        user = await BlockDao.find_one_or_none(blocked_user_id=user_id)
        if user:
            raise UserIsAlreadyBlockedException
        await BlockDao.add(
            blocked_user_id=user_id, reason=reason, moderator_id=moderator_id
        )
        response_data = {
            "detail": "The user has been blocked.",
            "blocked_user_id": user_id,
        }
        return response_data
