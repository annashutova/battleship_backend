from pydantic import BaseModel


class UserInfo(BaseModel):
    username: int


class UserLoginResponse(BaseModel):
    access_token: str
