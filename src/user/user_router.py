from datetime import timedelta, datetime

from passlib.context import CryptContext
from typing import Annotated
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from starlette import status
from starlette.responses import RedirectResponse

from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/user", tags=["user"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
SECRET_KEY = 'be924f8a12a3e023bb576eb1e9c022b7975ddcc95ae938e31944f78164617c19'
ALGORITHM = "HS256"


def get_current_user(token: str, db: Annotated[Session, Depends(get_db)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    else:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        return user


@router.get("/register", name="create_user")
def create_user(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", status_code=status.HTTP_204_NO_CONTENT)
def post_create_user(username: Annotated[str, Form()],
                     email: Annotated[str, Form()],
                     password1: Annotated[str, Form()],
                     db: Annotated[Session, Depends(get_db)]):

    user = db.query(User).filter(User.username == username).first()

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
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="아이디 혹은 비밀번호가 일치하지 않습니다.",
                            headers={"WWW-Authenticate": "Bearer"},
                            )
    # make access token
    data = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


@router.get("/logout", name="logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response