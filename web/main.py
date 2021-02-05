"""Web"""
from datetime import timedelta

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient

from auth import authenticate_user, users_db, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user
from models import Token, User

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

mongo_db = MongoClient('mongodb://mongo').instaimg
configs_db = mongo_db.configs
errors_db = mongo_db.errors


@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Check username and password and return a token"""
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/errors")
def get_errors(current_user: User = Depends(get_current_user)):
    """Get errors"""
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
def mark_as_solved(error_id: str, current_user: User = Depends(get_current_user)):
    """Mark error as solved"""
    error = errors_db.find_one(ObjectId(error_id))
    if error:
        errors_db.update_one({'_id': error['_id']}, {'$set': {'solved': True}})


@app.get("/api/users/count")
def get_users_count(current_user: User = Depends(get_current_user)):
    """Get Bot users count"""
    return configs_db.find().count()


#
# HTMl Responses
#

@app.get("/", response_class=HTMLResponse)
def index():
    """Index page"""
    return RedirectResponse('/errors')


@app.get("/errors", response_class=HTMLResponse)
def errors(request: Request):
    """Errors page"""
    return templates.TemplateResponse("errors.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})
