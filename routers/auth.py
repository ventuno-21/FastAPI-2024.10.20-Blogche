from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from starlette import status
from db.database import db_dependency
from db.models import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from starlette.responses import RedirectResponse

router = APIRouter(prefix='/auth', tags=['auth'])

templates = Jinja2Templates(directory='templates')

ALGORITHM = 'HS256'
SECRET_KEY = 'yoursecretkey'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

    class config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oath_form(self):
        form = await self.request.form()
        self.username = form.get('username')
        self.password = form.get('password')


# Decode JWT token (Contain Header, Payload and Signature, only header and payload can be decoded because they
# both are encoded base on base64)
# Header contains type of: 1)Type of the algorithm which we use to encode and 2) type of our token
# Payload contains what ever information we use to encode
async def get_current_user(request: Request):
    try:
        token = request.cookies.get('access_token')
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get('id')
        username: str = payload.get('username')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
        return {'id': user_id, 'username': username, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')


#
@router.post("/create/user")
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = User(
        email=create_user_request.email,
        username=create_user_request.username,
        firstname=create_user_request.first_name,
        lastname=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
        phone_number=create_user_request.phone_number
    )

    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)

    return create_user_model


# Create JWT token and set_cookie
@router.post("/token", response_model=Token)
async def login_to_create_token(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                db: db_dependency):
    user = db.query(User).filter(User.username == form_data.username).first()
    # print(user)
    if not user:
        return False

    if not bcrypt_context.verify(form_data.password, user.hashed_password):
        return False

    expires = datetime.now(timezone.utc) + timedelta(minutes=34)

    encode = {'id': user.id, 'username': user.username, 'role': user.role, 'exp': expires}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    response.set_cookie(
        key='access_token',
        value=token,
        httponly=True,
        max_age=1800,
        expires=1800)
    return True


@router.get("/login-page")
def login_user(request: Request):
    if request.state.is_authenticated:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login-page", response_class=HTMLResponse)
async def login_user(request: Request, db: db_dependency):
    try:
        form = LoginForm(request)
        await form.create_oath_form()
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_to_create_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Incorrect username or password"
            return templates.TemplateResponse("login.html", {'request': request, 'msg': msg})
        return response
    except HTTPException:
        msg = "Unknown error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

"""
REGISTER USER PAGE - GET METHOD
"""
@router.get("/register-page", response_class=HTMLResponse)
def register_user(request: Request):
    if request.state.is_authenticated:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register-page", response_class=HTMLResponse)
def register_user(request: Request, username: Annotated[str, Form()], password1: Annotated[str, Form()],
                  password2: Annotated[str, Form()], email: Annotated[str, Form()], db: db_dependency):
    validation1 = db.query(User).filter(User.username == username).first()
    validation2 = db.query(User).filter(User.email == email).first()

    if password1 != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid username, email or password, please check again"
        return templates.TemplateResponse('register.html', {'request': request, 'msg': msg})

    user = User(
        email=email,
        username=username,
        role="client",
        hashed_password=bcrypt_context.hash(password1),
        is_active=True)

    db.add(user)
    db.commit()
    db.refresh(user)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get("/change-pass", response_class=HTMLResponse)
def change_password(request: Request):
    print("inside change pass get method")

    return templates.TemplateResponse("change_password.html", {"request": request})


@router.post("/change-pass", response_class=HTMLResponse)
def change_password(request: Request, db: db_dependency, password1: Annotated[str, Form()],
                    password2: Annotated[str, Form()], current_pass: Annotated[str, Form()]):
    print("inside change pass")
    if request.state.is_authenticated:
        username = request.state.username
        user = db.query(User).filter(User.username == username).first()
        print(" user is authenticated")
        if not bcrypt_context.verify(current_pass, user.hashed_password) or password1 != password2:
            msg = "You may type wrong password or new password doens't match with confirmation of it!"
            return templates.TemplateResponse('change_password.html', {'request': request, 'msg': msg})
        else:
            print(" pass is authenticated")
            user.hashed_password = bcrypt_context.hash(password1)
            db.add(user)
            db.commit()
            db.refresh(user)
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get("/logout", response_class=HTMLResponse)
def logout_user(request: Request):
    response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    # print("logout response included:")
    print("response.__dict__=")
    print(response.__dict__)
    print("response.__dir__=")
    print(response.__dir__)
    print("response=")
    print(response)
    print(dir(response))
    response.delete_cookie("access_token")
    return response
