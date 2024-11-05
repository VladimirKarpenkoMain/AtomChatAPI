from fastapi import Depends, WebSocket, status
from fastapi.exceptions import WebSocketException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.auth.auth_utilits import (
    ACCESS_TOKEN_TYPE,
    decode_jwt,
    validate_token_type,
    validate_user_from_payload,
)
from app.auth.models import User
from app.core.exceptions import (
    IncorrectTokenFormatException,
    TokenExpiredException,
    UserIsNotModeratorException,
)

# Инициализация схемы авторизации с использованием HTTP Bearer токена
http_bearer = HTTPBearer()


# Функция для декодирования и проверки JWT токена, передаваемого в HTTP заголовке
def get_current_payload(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    """
    Декодирует и возвращает полезную нагрузку (payload) JWT токена из HTTP заголовков.
    :param credentials: Данные авторизации (Bearer токен).
    :raises TokenExpiredException: Если токен истек.
    :raises IncorrectTokenFormatException: Если токен недействителен.
    :return: Полезная нагрузка токена (payload).
    """
    try:
        payload = decode_jwt(token=credentials.credentials)
        return payload
    except ExpiredSignatureError:
        # Если срок действия токена истек
        raise TokenExpiredException
    except InvalidTokenError:
        # Если формат токена неверен
        raise IncorrectTokenFormatException


# Функция для получения текущего пользователя на основе полезной нагрузки JWT
async def get_current_user(payload: dict = Depends(get_current_payload)):
    """
    Возвращает объект пользователя, декодируя и проверяя полезную нагрузку токена.
    :param payload: Полезная нагрузка токена, полученная из get_current_payload.
    :raises NotValidTokenTypeException: Если тип токена не соответствует ожидаемому.
    :return: Объект пользователя.
    """
    # Проверка типа токена (требуется токен доступа)
    validate_token_type(payload, ACCESS_TOKEN_TYPE)
    # Валидация пользователя на основе данных в payload
    user = await validate_user_from_payload(payload)
    return user


# Функция для получения текущего пользователя по WebSocket соединению
async def get_current_user_websocket(websocket: WebSocket):
    """
    Получает текущего пользователя через WebSocket, декодируя и проверяя токен в заголовках.
    :param websocket: WebSocket соединение.
    :raises WebSocketException: Если токен отсутствует, истек, имеет неверный формат или неверный тип.
    :return: Объект пользователя.
    """
    # Извлечение токена из заголовка WebSocket соединения
    token = websocket.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Authorization token missing."
        )

    # Извлечение самого токена
    token = token.split(" ")[1]
    try:
        # Декодирование и проверка токена
        payload = decode_jwt(token=token)
        validate_token_type(payload, ACCESS_TOKEN_TYPE, websocket_mode=True)
        # Валидация пользователя на основе полезной нагрузки
        user = await validate_user_from_payload(payload, websocket_mode=True)
        return user
    except ExpiredSignatureError:
        # Обработка истекшего токена
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="The token has expired."
        )
    except InvalidTokenError:
        # Обработка неверного формата токена
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token format."
        )


# Функция для получения текущего пользователя, являющегося модератором
async def get_moderator_user(user: User = Depends(get_current_user)):
    """
    Проверяет, является ли текущий пользователь модератором.
    :param user: Объект пользователя, полученный через get_current_user.
    :raises UserIsNotModeratorException: Если пользователь не является модератором.
    :return: Объект пользователя, если он является модератором.
    """
    if user.is_moderator:
        return user
    # Если пользователь не модератор, выбрасывается исключение
    raise UserIsNotModeratorException()
