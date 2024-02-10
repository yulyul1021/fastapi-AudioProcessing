import os
from datetime import timedelta, datetime
from dotenv import load_dotenv

from passlib.context import CryptContext
from typing import Annotated
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from starlette import status
from starlette.responses import RedirectResponse

from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/user", tags=["user"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


@router.get("/register", name="create_user")
def create_user(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", status_code=status.HTTP_204_NO_CONTENT)
def post_create_user(username: Annotated[str, Form()],
                     email: Annotated[str, Form()],
                     password1: Annotated[str, Form()],
                     db: Annotated[Session, Depends(get_db)]):

    user = db.query(User).filter(User.username == username)

    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 회원입니다.")

    db_user = User(username=username,
                   password=pwd_context.hash(password1),
                   email=email)
    db.add(db_user)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", name="login")
def user_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def post_user_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                    db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.username == form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="아이디 혹은 비밀번호가 일치하지 않습니다.")

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

