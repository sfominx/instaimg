"""
Web Data Models
"""
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    password: str


class DBUser(BaseModel):
    username: str
    hashed_password: str
