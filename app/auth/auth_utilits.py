from datetime import datetime, timedelta

import jwt
from fastapi import WebSocketException, status
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from pydantic import EmailStr

from app.auth.dao import BlockDao, UsersDao
from app.auth.shemas import STokenInfo, SUserAuth
from app.core.config import settings
from app.core.exceptions import (
    IncorrectTokenFormatException,
    NotValidTokenTypeException,
    TokenExpiredException,
    TokensDoesNotMatchException,
    UserIsBlockedException,
    UserIsNotPresentException,
)

# Поля и значения, определяющие типы токенов
TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Конфигурация контекста для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Проверка пароля: сверяет обычный пароль с его хешем
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Генерация хеша для пароля
def get_password_hash(password):
    return pwd_context.hash(password)


# Кодирование JWT токена
def encode_jwt(
    payload: dict,
    private_key: str = settings.AUTH_JWT.PRIVATE_KEY_PATH.read_text(),
    algorithm: str = settings.AUTH_JWT.ALGORITHM,
    expire_minutes: int = settings.AUTH_JWT.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: timedelta | None = None,
) -> str:
    """
    Кодирует и возвращает JWT токен с заданной полезной нагрузкой и временем истечения.
    :param payload: Данные для кодирования в токен
    :param private_key: Приватный ключ для подписи токена
    :param algorithm: Алгоритм кодирования
    :param expire_minutes: Время истечения в минутах, если не указано время истечения
    :param expire_timedelta: Временной интервал для истечения, если задан
    :return: Закодированный JWT токен
    """
    to_encode = payload.copy()
    now = datetime.utcnow()
    # Определяем время истечения токена
    expire = (
        now + expire_timedelta
        if expire_timedelta
        else now + timedelta(minutes=expire_minutes)
    )
    to_encode.update(exp=expire, iat=now)
    encoded = jwt.encode(payload=to_encode, key=private_key, algorithm=algorithm)
    return encoded


# Декодирование JWT токена
def decode_jwt(
    token: str | bytes,
    public_key: str = settings.AUTH_JWT.PUBLIC_KEY_PATH.read_text(),
    algorithm: str = settings.AUTH_JWT.ALGORITHM,
):
    """
    Декодирует и возвращает данные JWT токена.
    :param token: Закодированный JWT токен
    :param public_key: Публичный ключ для проверки подписи токена
    :param algorithm: Алгоритм декодирования
    :return: Декодированная полезная нагрузка токена
    """
    decoded = jwt.decode(jwt=token, key=public_key, algorithms=[algorithm])
    return decoded


# Создание JWT токена определенного типа (access или refresh)
def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int = settings.AUTH_JWT.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: timedelta | None = None,
) -> str:
    """
    Создает и возвращает JWT токен с заданным типом.
    :param token_type: Тип токена ('access' или 'refresh')
    :param token_data: Данные для включения в токен
    :param expire_minutes: Время истечения токена в минутах
    :param expire_timedelta: Временной интервал для истечения, если задан
    :return: Закодированный JWT токен
    """
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)
    return encode_jwt(
        jwt_payload, expire_minutes=expire_minutes, expire_timedelta=expire_timedelta
    )


# Создание access токена для пользователя
def create_access_token(user: SUserAuth):
    jwt_payload = {"sub": str(user.id)}
    return create_jwt(token_type=ACCESS_TOKEN_TYPE, token_data=jwt_payload)


# Создание refresh токена для пользователя
def create_refresh_token(user: SUserAuth):
    jwt_payload = {"sub": str(user.id)}
    expire_timedelta = timedelta(days=settings.AUTH_JWT.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=expire_timedelta,
    )


# Валидация пользователя из полезной нагрузки токена
async def validate_user_from_payload(payload: dict, websocket_mode: bool = False):
    """
    Проверяет, существует ли пользователь из полезной нагрузки токена и не заблокирован ли он.
    :param payload: Полезная нагрузка токена
    :param websocket_mode: Режим WebSocket для передачи исключений как WebSocketException
    :return: Объект пользователя, если пользователь существует и не заблокирован
    """
    user_id: str = payload.get("sub")
    if not user_id:
        if websocket_mode:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        raise UserIsNotPresentException

    user = await UsersDao.find_by_id(user_id)
    if not user:
        if websocket_mode:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        raise UserIsNotPresentException

    # Проверка, заблокирован ли пользователь
    block = await BlockDao.find_one_or_none(blocked_user_id=user_id)
    if block:
        if websocket_mode:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="The user was blocked."
            )
        raise UserIsBlockedException

    return user


# Проверка типа токена
def validate_token_type(
    payload: dict, excepted_token_type: str, websocket_mode: bool = False
):
    """
    Проверяет, соответствует ли тип токена ожидаемому.
    :param payload: Полезная нагрузка токена
    :param excepted_token_type: Ожидаемый тип токена ('access' или 'refresh')
    :param websocket_mode: Режим WebSocket для передачи исключений как WebSocketException
    """
    token_type: str = payload.get(TOKEN_TYPE_FIELD)
    if token_type != excepted_token_type:
        if websocket_mode:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"Invalid token type {token_type!r}, expected {excepted_token_type!r}.",
            )
        raise NotValidTokenTypeException(token_type, excepted_token_type)


# Аутентификация пользователя по email и паролю
async def authentication(email: EmailStr, password: str):
    """
    Проверяет существование пользователя по email и корректность пароля.
    :param email: Email пользователя
    :param password: Пароль пользователя
    :return: Объект пользователя, если аутентификация успешна, иначе None
    """
    user = await UsersDao.find_one_or_none(email=email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    if await BlockDao.find_one_or_none():
        raise UserIsBlockedException
    return user


# Обновление токенов с использованием refresh токена
async def refresh(refresh_token: str):
    """
    Обновляет access и refresh токены для пользователя.
    :param refresh_token: Текущий refresh токен пользователя
    :return: Новый объект STokenInfo с новыми access и refresh токенами
    """
    try:
        # Расшифровка токена и проверка его валидности
        payload = decode_jwt(refresh_token)
        validate_token_type(payload, REFRESH_TOKEN_TYPE)
        user = await validate_user_from_payload(payload)

        # Проверка, что refresh токен совпадает с тем, что хранится в БД
        if user.refresh_token != refresh_token:
            raise TokensDoesNotMatchException

        # Генерация новых токенов
        new_access_token = create_access_token(user)
        new_refresh_token = create_refresh_token(user)

        # Обновление refresh токена в БД
        await UsersDao.update_refresh_token(user.id, new_refresh_token)

        return STokenInfo(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    except ExpiredSignatureError:
        raise TokenExpiredException
    except InvalidTokenError:
        raise IncorrectTokenFormatException
