from fastapi import HTTPException, status
from pydantic import UUID4

from app.core.logger import logger


class BaseException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

# Пользователи
class UserEmailExistsException(BaseException):
    status_code = status.HTTP_409_CONFLICT
    detail = 'A user with such an email exists.'

class UserUsernameExistsException(BaseException):
    status_code = status.HTTP_409_CONFLICT
    detail = 'A user with such an username exists.'

class PasswordsDoesNotMatchException(BaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Passwords don't match."

class IncorrectEmailOrPasswordException(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Invalid email or password.'

class TokenExpiredException(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail='The token has expired.'

class TokenAbsentException(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'The access token is missing.'

class IncorrectTokenFormatException(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Invalid token format.'

class TokensDoesNotMatchException(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Invalid token. Please log in again.'

class UserIsNotPresentException(BaseException):
    status_code = status.HTTP_401_UNAUTHORIZED

class NotValidTokenTypeException(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, invalid_token_type: str, excepted_token_type: str):
        self.detail = f'Invalid token type {invalid_token_type!r}, excepted {excepted_token_type!r}.'
        super().__init__(status_code=self.status_code, detail=self.detail)

class UserIsAlreadyBlockedException(BaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "The user is already blocked."

class UserIsBlockedException(BaseException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "The user was blocked."

class UserIsNotModeratorException(BaseException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You don’t have permission to access."

# Чат
class OneUserIdNotFoundException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, user_id: UUID4):
        self.detail = {
            "message": f'The user with this IDs was not found.',
            "not_found_id": str(user_id)
        }
        super().__init__(status_code=self.status_code, detail=self.detail)

class UsersIdNotFoundException(BaseException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No users with such IDs were found."

class UserSearchNotFoundException(BaseException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Users not found."

class UserMessagesBetweenSameException(BaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "It is not possible to receive messages between the current user and the same user."

class UserMessagesBetweenYourselfException(BaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "The user cannot send messages to himself."

class ErrorHandler:
    _type_error: Exception = None
    _type_error_message: str = None
    @classmethod
    def _log_error(cls, e: Exception, error_message: str, extra: dict = None):
        if isinstance(e, cls._type_error):
            msg = cls._type_error_message
        else:
            msg = "Unknown Error"
        msg = msg + ": " + error_message
        logger.error(msg, extra=extra, exc_info=True)