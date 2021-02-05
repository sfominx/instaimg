"""
Auth routine
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from models import DBUser, TokenData
from secrets import JWT_SECRET_KEY, ADMIN_PASSWORD

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": ADMIN_PASSWORD
    }
}


def verify_password(plain_password, hashed_password):
    """Check entered password equals stored one"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Get bcrypt password hash"""
    return pwd_context.hash(password)


def get_user(database, username: str):
    """Get user from DB"""
    if username in database:
        user_dict = database[username]
        return DBUser(**user_dict)
    return None


def authenticate_user(fake_db, username: str, password: str):
    """Check user exists and passord is Ok"""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Check user auth and return it"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception from None
    user = get_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
