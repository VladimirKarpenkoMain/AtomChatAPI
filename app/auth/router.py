from fastapi import APIRouter, status
from app.auth.shemas import SUserAuth, STokenInfo, SUserRegisterResponse, SRefreshToken, SUserRegister
from app.auth.dao import UsersDao
from app.auth.auth_utilits import get_password_hash, authentication, create_access_token, create_refresh_token, refresh
from app.core.exceptions import UserEmailExistsException, IncorrectEmailOrPasswordException, PasswordsDoesNotMatchException, \
    UserUsernameExistsException

router = APIRouter(
    prefix='/auth',
    tags=['Auth & Пользователи'],
)

@router.post('/register/', status_code=status.HTTP_201_CREATED, response_model=SUserRegisterResponse)
async def register_user(user_data: SUserRegister):
    existing_user = await UsersDao.find_by_email_or_username(email=user_data.email, username=user_data.username)
    if existing_user:
        if existing_user.email == user_data.email:
            raise UserEmailExistsException
        if existing_user.username == user_data.username:
            raise UserUsernameExistsException
    if user_data.password != user_data.password_repiet:
        raise PasswordsDoesNotMatchException
    hashed_password = get_password_hash(user_data.password)
    await UsersDao.add(email=user_data.email, username=user_data.username, hashed_password=hashed_password)
    return {'detail': 'The user has been registered successfully.'}

@router.post('/login/', response_model=STokenInfo)
async def jwt_login_user(user_data: SUserAuth):
    user = await authentication(user_data.email, user_data.password)
    if user is None:
        raise IncorrectEmailOrPasswordException

    access_token: str = create_access_token(user)
    refresh_token: str = create_refresh_token(user)
    await UsersDao.update_refresh_token(user_id=user.id, token=refresh_token)
    return STokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post('/refresh/', response_model=STokenInfo)
async def jwt_refresh_token(refresh_token: SRefreshToken):
    result = await refresh(refresh_token=refresh_token.refresh_token)
    return result