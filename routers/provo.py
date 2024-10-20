from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, File, UploadFile
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
import pybase64

router = APIRouter(prefix='/provo', tags=['provo'])

templates = Jinja2Templates(directory='templates')


@router.post("/upload")
async def upload(filename: Annotated[str, Form()], filedata: Annotated[str, Form()]):
    image_as_bytes = str.encode(filedata)  # convert string to bytes
    img_recovered = pybase64.b64decode(image_as_bytes)  # decode base64string
    print(img_recovered)
    print("="*100)
    print("upload post function")
    with open("uploaded_" + filename, "wb") as f:
        f.write(img_recovered)
    return {"message": f"Successfuly uploaded {filename}"}


@router.get("/")
async def main(request: Request):
    print("&"*100)
    print("upload get function")
    return templates.TemplateResponse("provo.html", {"request": request})