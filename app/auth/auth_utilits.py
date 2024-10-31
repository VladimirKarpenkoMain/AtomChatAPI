from datetime import datetime, timedelta

import jwt
from fastapi import WebSocketException, status
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from pydantic import EmailStr

from app.core.exceptions import UserIsNotPresentException, NotValidTokenTypeException, IncorrectTokenFormatException, \
    TokenExpiredException, TokensDoesNotMatchException, UserIsBlockedException
from app.auth.dao import UsersDao, BlockDao
from app.core.config import settings
from app.auth.shemas import SUserAuth, STokenInfo

TOKEN_TYPE_FIELD = 'type'
ACCESS_TOKEN_TYPE = 'access'
REFRESH_TOKEN_TYPE = 'refresh'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def encode_jwt(payload: dict,
               private_key: str = settings.AUTH_JWT.PRIVATE_KEY_PATH.read_text(),
               algorithm: str = settings.AUTH_JWT.ALGORITHM,
               expire_minutes: int = settings.AUTH_JWT.ACCESS_TOKEN_EXPIRE_MINUTES,
               expire_timedelta: timedelta | None = None) -> str:
    to_encode = payload.copy()
    now = datetime.utcnow()
    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expire_minutes)
    to_encode.update(
        exp=expire,
        iat=now,
    )
    encoded = jwt.encode(payload=to_encode, key=private_key, algorithm=algorithm)
    return encoded

def decode_jwt(token: str | bytes,
               public_key: str = settings.AUTH_JWT.PUBLIC_KEY_PATH.read_text(),
               algorithm: str =settings.AUTH_JWT.ALGORITHM):
    decoded = jwt.decode(jwt=token, key=public_key, algorithms=[algorithm])
    return decoded

def create_jwt(
        token_type: str,
        token_data: dict,
        expire_minutes: int = settings.AUTH_JWT.ACCESS_TOKEN_EXPIRE_MINUTES,
        expire_timedelta: timedelta | None = None
) -> str:
    jwt_payload = {
        TOKEN_TYPE_FIELD: token_type
    }
    jwt_payload.update(token_data)
    return encode_jwt(jwt_payload, expire_minutes=expire_minutes, expire_timedelta=expire_timedelta)

def create_access_token(user: SUserAuth):
    jwt_payload = {
        'sub': str(user.id)
    }
    return create_jwt(token_type=ACCESS_TOKEN_TYPE, token_data=jwt_payload)

def create_refresh_token(user: SUserAuth):
    jwt_payload = {
        'sub': str(user.id)
    }
    expire_timedelta = timedelta(days=settings.AUTH_JWT.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_jwt(token_type=REFRESH_TOKEN_TYPE, token_data=jwt_payload, expire_timedelta=expire_timedelta)


async def validate_user_from_payload(payload: dict, websocket_mode: bool = False):
    user_id: str = payload.get('sub')
    if not user_id:
        if websocket_mode:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        raise UserIsNotPresentException
    user = await UsersDao.find_by_id(user_id)
    if not user:
        if websocket_mode:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        raise UserIsNotPresentException
    block = await BlockDao.find_one_or_none(blocked_user_id=user_id)
    if block:
        if websocket_mode:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="The user was blocked.")
        raise UserIsBlockedException
    return user

def validate_token_type(payload: dict, excepted_token_type: str, websocket_mode: bool = False):
    token_type: str = payload.get(TOKEN_TYPE_FIELD)
    if token_type != excepted_token_type:
        if websocket_mode:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=f'Invalid token type {token_type!r}, excepted {excepted_token_type!r}.')
        raise NotValidTokenTypeException(token_type, excepted_token_type)

async def authentication(email: EmailStr, password: str):
    user = await UsersDao.find_one_or_none(email=email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    if await BlockDao.find_one_or_none():
        raise UserIsBlockedException
    return user

async def refresh(refresh_token: str):
    try:
        # Расшифровка токена и проверка его валидности
        payload = decode_jwt(refresh_token)
        validate_token_type(payload, REFRESH_TOKEN_TYPE)
        user = await validate_user_from_payload(payload)

        # Проверяем, что refresh token совпадает с тем, что хранится в БД
        if user.refresh_token != refresh_token:
            raise TokensDoesNotMatchException

        # Генерация новых токенов
        new_access_token = create_access_token(user)
        new_refresh_token = create_refresh_token(user)

        # Обновляем refresh token в БД
        await UsersDao.update_refresh_token(user.id, new_refresh_token)

        return STokenInfo(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    except ExpiredSignatureError:
        raise TokenExpiredException
    except InvalidTokenError:
        raise IncorrectTokenFormatException
