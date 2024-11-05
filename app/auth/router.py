from fastapi import APIRouter, status

from app.auth.services import AuthService
from app.auth.shemas import (
    SRefreshToken,
    STokenInfo,
    SUserAuth,
    SUserRegister,
    SUserRegisterResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth & Users"],
)


@router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=SUserRegisterResponse,
)
async def register_user(user_data: SUserRegister):
    """
    Регистрация нового пользователя.

    Этот эндпоинт позволяет зарегистрировать нового пользователя, используя предоставленные данные.

    - **user_data**: Информация, необходимая для регистрации пользователя.

    Возвращает сообщение об успешной регистрации.
    """
    return await AuthService.register_user(user_data)


@router.post("/login/", response_model=STokenInfo)
async def jwt_login_user(user_data: SUserAuth):
    """
    Авторизация пользователя.

    Этот эндпоинт позволяет авторизовать пользователя и получить JWT токены.

    - **user_data**: Данные пользователя для авторизации.

    Возвращает объект с access и refresh токенами.
    """
    return await AuthService.jwt_login_user(user_data)


@router.post("/refresh/", response_model=STokenInfo)
async def jwt_refresh_token(refresh_token: SRefreshToken):
    """
    Обновление JWT токенов.

    Этот эндпоинт позволяет обновить JWT токены с использованием действующего refresh токена.

    - **refresh_token**: Refresh токен для обновления.

    Возвращает обновленные access и refresh токены.
    """
    return await AuthService.jwt_refresh_token(refresh_token)
