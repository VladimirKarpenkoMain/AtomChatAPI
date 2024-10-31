from annotated_types import MinLen, MaxLen
from pydantic import BaseModel, EmailStr, UUID4
from typing_extensions import Annotated

from app.auth.models import Blocked


class SUserAuth(BaseModel):
    email: EmailStr
    password: Annotated[str, MinLen(8), MaxLen(128)]

class SUserRegister(BaseModel):
    email: EmailStr
    username: Annotated[str, MinLen(5), MaxLen(50)]
    password: Annotated[str, MinLen(8), MaxLen(128)]
    password_repiet: Annotated[str, MinLen(8), MaxLen(128)]

class SUserRegisterResponse(BaseModel):
    detail: str = 'The user has been registered successfully.'


class STokenInfo(BaseModel):
    access_token: str
    refresh_token: str

class SRefreshToken(BaseModel):
    refresh_token: str

class SBlock(BaseModel):
    user_id: UUID4
    reason_of_block: Annotated[str, MinLen(10), MaxLen(256)]