from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str


class UserLogin(BaseModel):
    username: str
    password: str
