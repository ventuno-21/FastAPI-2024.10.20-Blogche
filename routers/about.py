from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from starlette import status
from sqlalchemy import desc
from db.database import db_dependency
from db.models import User, Post, Comment
from passlib.context import CryptContext
from jose import jwt, JWTError
from starlette.responses import RedirectResponse
from string import ascii_letters
import random
import datetime
import imghdr

router = APIRouter(prefix='/about-us/contact', tags=['about-us'])

templates = Jinja2Templates(directory='templates')


@router.get("/", response_class=HTMLResponse)
def all_posts(request: Request, db: db_dependency):

    context = {
        'request':request,
    }
    return templates.TemplateResponse("about.html", context)