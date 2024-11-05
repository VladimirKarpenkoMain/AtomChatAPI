from fastapi import HTTPException, status
from pydantic import UUID4

from app.core.logger import logger


# Базовый класс для всех HTTP исключений в приложении
class BaseException(HTTPException):
    # Стандартный статусный код для базового исключения - ошибка сервера
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    # Детальное сообщение по умолчанию
    detail = ""

    def __init__(self):
        # Инициализация HTTPException с установленными статусом и деталями
        super().__init__(status_code=self.status_code, detail=self.detail)


# Исключения для работы с пользователями


class UserEmailExistsException(BaseException):
    # Исключение для ситуации, когда пользователь с данным email уже существует
    status_code = status.HTTP_409_CONFLICT
    detail = "A user with such an email exists."


class UserUsernameExistsException(BaseException):
    # Исключение для ситуации, когда пользователь с данным username уже существует
    status_code = status.HTTP_409_CONFLICT
    detail = "A user with such an username exists."


class PasswordsDoesNotMatchException(BaseException):
    # Исключение для случая, когда пароли не совпадают
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Passwords don't match."


class IncorrectEmailOrPasswordException(BaseException):
    # Исключение для случая неверного email или пароля
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password."


class TokenExpiredException(BaseException):
    # Исключение для случая истечения срока действия токена
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "The token has expired."


class TokenAbsentException(BaseException):
    # Исключение для случая отсутствия токена доступа
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "The access token is missing."


class IncorrectTokenFormatException(BaseException):
    # Исключение для случая неверного формата токена
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid token format."


class TokensDoesNotMatchException(BaseException):
    # Исключение для случая, когда токены не совпадают
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid token. Please log in again."


class UserIsNotPresentException(BaseException):
    # Исключение для случая, когда пользователь не найден в системе
    status_code = status.HTTP_401_UNAUTHORIZED


class NotValidTokenTypeException(HTTPException):
    # Исключение для случая, когда тип токена не соответствует ожидаемому
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, invalid_token_type: str, excepted_token_type: str):
        # Формирование детализированного сообщения об ошибке с указанием неверного и ожидаемого типов токенов
        self.detail = f"Invalid token type {invalid_token_type!r}, expected {excepted_token_type!r}."
        super().__init__(status_code=self.status_code, detail=self.detail)


class UserIsAlreadyBlockedException(BaseException):
    # Исключение для случая, когда пользователь уже заблокирован
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "The user is already blocked."


class UserIsBlockedException(BaseException):
    # Исключение для случая, когда пользователь заблокирован
    status_code = status.HTTP_403_FORBIDDEN
    detail = "The user was blocked."


class UserIsNotModeratorException(BaseException):
    # Исключение для случая, когда пользователь не имеет прав модератора
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You don’t have permission to access."


# Исключения для работы с чатом


class OneUserIdNotFoundException(HTTPException):
    # Исключение для случая, когда один из ID пользователей не найден
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, user_id: UUID4):
        # Формирование детализированного сообщения с указанием ID, который не был найден
        self.detail = {
            "message": "The user with this IDs was not found.",
            "not_found_id": str(user_id),
        }
        super().__init__(status_code=self.status_code, detail=self.detail)


class UsersIdNotFoundException(BaseException):
    # Исключение для случая, когда ни один из ID пользователей не найден
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No users with such IDs were found."


class UserSearchNotFoundException(BaseException):
    # Исключение для случая, когда пользователи не найдены по заданным критериям поиска
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Users not found."


class UserMessagesBetweenSameException(BaseException):
    # Исключение для случая, когда запрашиваются сообщения между текущим пользователем и ним же
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "It is not possible to receive messages between the current user and the same user."


class UserMessagesBetweenYourselfException(BaseException):
    # Исключение для случая, когда пользователь пытается отправить сообщение самому себе
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "The user cannot send messages to himself."


# Класс для обработки ошибок и логирования


class ErrorHandler:
    # Тип исключения, который будет использоваться для обработки ошибок
    _type_error: Exception | None = None
    # Часть сообщения об ошибке по умолчанию
    _type_error_message: str | None = None

    @classmethod
    def _log_error(cls, e: Exception, error_message: str, extra: dict | None = None):
        """
        Логирует ошибку с указанием сообщения и дополнительных данных.
        :param e: Исключение, которое произошло.
        :param error_message: Сообщение об ошибке.
        :param extra: Дополнительные данные для логирования.
        """
        # Если тип исключения соответствует _type_error, используем стандартное сообщение
        if isinstance(e, cls._type_error):
            msg = cls._type_error_message
        else:
            # Если тип исключения неизвестен, устанавливаем сообщение об "Неизвестной ошибке"
            msg = "Unknown Error"
        # Добавляем детализированное сообщение об ошибке
        msg = msg + ": " + error_message
        # Логируем сообщение с дополнительной информацией и исключением
        logger.error(msg, extra=extra, exc_info=True)
