from  datetime import timedelta, datetime
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError

from db.database import engine, Base
from db.models import User
from routers import auth, post, provo, about

app = FastAPI()
app.include_router(post.router)
app.include_router(auth.router)
app.include_router(provo.router)
app.include_router(about.router)

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

ALGORITHM = 'HS256'
SECRET_KEY = 'fastapi-insecure-9tw8u-qd)wh^&hltl(_u(l)s(%0r%_1by@tzc#evg437!oj%(-'


@app.middleware("http")
async def is_authenticated(request: Request, call_next):
    token = request.cookies.get('access_token')
    if token is None:
        request.state.is_authenticated = False
        request.state.username = None
    else:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('username')
        request.state.is_authenticated = True
        request.state.username = username

    response = await call_next(request)
    return response
