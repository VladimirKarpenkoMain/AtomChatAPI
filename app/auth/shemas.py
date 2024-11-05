from annotated_types import MaxLen, MinLen
from pydantic import UUID4, BaseModel, EmailStr, Field
from typing_extensions import Annotated


class SUserAuth(BaseModel):
    """
    Данные для авторизации пользователя.
    """

    email: EmailStr = Field(
        ...,
        example="example@domain.com",
        description="Email пользователя, проверяется на корректный формат.",
    )
    password: Annotated[str, MinLen(8), MaxLen(128)] = Field(
        ...,
        example="example_password",
        description="Пароль пользователя, длина от 8 до 128 символов.",
    )


class SUserRegister(BaseModel):
    """
    Данные для регистрации пользователя.
    """

    email: EmailStr = Field(
        ...,
        example="newuser@domain.com",
        description="Email пользователя для регистрации.",
    )
    username: Annotated[str, MinLen(5), MaxLen(50)] = Field(
        ...,
        example="new_username",
        description="Имя пользователя, длина от 5 до 50 символов.",
    )
    password: Annotated[str, MinLen(8), MaxLen(128)] = Field(
        ...,
        example="secure_password",
        description="Основной пароль, длиной от 8 до 128 символов.",
    )
    password_repiet: Annotated[str, MinLen(8), MaxLen(128)] = Field(
        ...,
        example="secure_password",
        description="Подтверждение пароля, должно совпадать с основным паролем.",
    )


class SUserRegisterResponse(BaseModel):
    """
    Ответ на успешную регистрацию пользователя.
    """

    detail: str = Field(
        default="The user has been registered successfully.",
        example="The user has been registered successfully.",
        description="Сообщение об успешной регистрации.",
    )


class STokenInfo(BaseModel):
    """
    Данные access и refresh токенов.
    """

    access_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        description="Access-токен для авторизации пользователя.",
    )
    refresh_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        description="Refresh-токен для обновления access-токена.",
    )


class SRefreshToken(BaseModel):
    """
    Данные для обновления access токена.
    """

    refresh_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        description="Refresh-токен для обновления access-токена.",
    )


class SBlock(BaseModel):
    """
    Данные для блокировки пользователя.
    """

    user_id: UUID4 = Field(
        ...,
        example="123e4567-e89b-12d3-a456-426614174000",
        description="ID пользователя для блокировки.",
    )
    reason_of_block: Annotated[str, MinLen(10), MaxLen(256)] = Field(
        ...,
        example="Spamming and violating community guidelines",
        description="Причина блокировки, длиной от 10 до 256 символов.",
    )
