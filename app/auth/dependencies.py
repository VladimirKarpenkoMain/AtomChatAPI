from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, WebSocket, status
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi.exceptions import WebSocketException

from app.auth.models import User
from app.core.exceptions import TokenExpiredException, IncorrectTokenFormatException, UserIsNotModeratorException
from app.auth.auth_utilits import decode_jwt, ACCESS_TOKEN_TYPE, validate_user_from_payload, validate_token_type

http_bearer = HTTPBearer()

def get_current_payload(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    try:
        payload = decode_jwt(token=credentials.credentials)
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredException
    except InvalidTokenError:
        raise IncorrectTokenFormatException

async def get_current_user(payload: dict = Depends(get_current_payload)):
    validate_token_type(payload, ACCESS_TOKEN_TYPE)
    user = await validate_user_from_payload(payload)
    return user

async def get_current_user_websocket(websocket: WebSocket):
    token = websocket.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Authorization token missing.")
    token = token.split(" ")[1]
    try:
        payload = decode_jwt(token=token)
        validate_token_type(payload, ACCESS_TOKEN_TYPE, websocket_mode=True)
        user = await validate_user_from_payload(payload, websocket_mode=True)
        return user
    except ExpiredSignatureError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="The token has expired.")
    except InvalidTokenError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token format.")

async def get_moderator_user(user: User = Depends(get_current_user)):
    if user.is_moderator:
        return user
    raise UserIsNotModeratorException()

