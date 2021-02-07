"""Web"""

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException, JWTDecodeError
from pydantic.main import BaseModel
from pymongo import MongoClient

from auth import authenticate_user, users_db
from models import User
from secrets import JWT_SECRET_KEY

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

mongo_db = MongoClient('mongodb://mongo').instaimg
configs_db = mongo_db.configs
errors_db = mongo_db.errors


#
# Auth routine
#

class Settings(BaseModel):
    authjwt_secret_key: str = JWT_SECRET_KEY
    authjwt_token_location: set = {"cookies"}


@AuthJWT.load_config
def get_config():
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    if isinstance(exc, JWTDecodeError) and 'expired' in exc.message:
        return RedirectResponse('/login')
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.post("/api/token")
def login_for_access_token(form_data: User, authorize: AuthJWT = Depends()):
    """Check username and password and return a token"""
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = authorize.create_access_token(subject=form_data.username)
    authorize.set_access_cookies(access_token)
    return {"msg": "Successfully login"}


@app.delete('/api/logout')
def logout(authorize: AuthJWT = Depends()):
    """
    Because the JWT are stored in an httponly cookie now, we cannot
    log the user out by simply deleting the cookies in the frontend.
    We need the backend to send us a response to delete the cookies.
    """
    authorize.jwt_required()

    authorize.unset_jwt_cookies()
    return {"msg": "Successfully logout"}


#
# API
#

@app.get("/api/errors")
def get_errors(authorize: AuthJWT = Depends()):
    """Get errors"""
    authorize.jwt_required()
    found_errors = []
    for error in errors_db.find({'solved': False}):
        list_error = {'chat_id': error['chat_id'],
                      'type': error['type'],
                      'timestamp': error['timestamp'],
                      'msg': error['msg'],
                      'id': str(error['_id'])}
        found_errors.append(list_error)
    return found_errors


@app.get("/api/mark_as_solved")
def mark_as_solved(error_id: str, authorize: AuthJWT = Depends()):
    """Mark error as solved"""
    authorize.jwt_required()
    error = errors_db.find_one(ObjectId(error_id))
    if error:
        errors_db.update_one({'_id': error['_id']}, {'$set': {'solved': True}})


@app.get("/api/users/count")
def get_users_count(authorize: AuthJWT = Depends()):
    """Get Bot users count"""
    authorize.jwt_required()
    return configs_db.find().count()


#
# HTMl Responses
#

@app.get("/")
def index():
    """Index page"""
    return RedirectResponse('/errors')


@app.get("/errors")
def errors(request: Request, authorize: AuthJWT = Depends()):
    """Errors page"""
    authorize.jwt_optional()

    if not authorize.get_jwt_subject():
        return RedirectResponse('/login')
    return templates.TemplateResponse("errors.html", {"request": request})


@app.get("/login")
def login(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})
