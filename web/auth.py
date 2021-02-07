"""
Auth routine
"""
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from models import DBUser
from secrets import ADMIN_PASSWORD

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
