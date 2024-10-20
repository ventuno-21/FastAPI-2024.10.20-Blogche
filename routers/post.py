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

router = APIRouter(prefix='', tags=['blog'])

templates = Jinja2Templates(directory='templates')


@router.get("/", response_class=HTMLResponse)
def all_posts(request: Request, db: db_dependency):
    posts = db.query(Post).order_by(desc(Post.timestamp)).all()
    context = {
        "request": request,
        "posts": posts
    }
    print("|-" * 50)
    print("blog home page get function:")
    print(f"request.state= {list(request)}")
    print(f"request.client.host= {request.client.host}")  # get ip address
    print(f"request.url.path= {request.url.path}")  # get path
    print(f"request.url= {request.url}")
    print(f"request.client= {request.client}")
    print(f"request.app= {request.app}")
    if request.state.is_authenticated:
        print(f"request.state= {request.state}")
        print(f"request.state.is_authenticated= {request.state.is_authenticated}")
        print(f"request.state.username= {request.state.username}")

    return templates.TemplateResponse("blog.html", context)


@router.get("/{post_id}")
async def single_post(request: Request, post_id: int, db: db_dependency):
    post = db.query(Post).filter(Post.id == post_id).first()
    recent_posts = db.query(Post).order_by(desc(Post.timestamp)).limit(5).all()
    context = {
        "request": request,
        "post": post,
        'recent_posts': recent_posts,
    }
    return templates.TemplateResponse("blog_details.html", context)


@router.post("/{post_id}")
async def add_comment(request: Request, post_id: int, db: db_dependency, comment: Annotated[str, Form()]):
    if request.state.is_authenticated:
        username = request.state.username
        print(username)
        user = db.query(User).filter(User.username == username).first()
        print(user.id)
        print(post_id)
        new_comment = Comment(
            text=comment,
            user_id=user.id,
            post_id=post_id,
            timestamp=datetime.datetime.now(),
        )
        print(new_comment)
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)

    url = f"/{post_id}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/post/create-post")
async def create_post(request: Request, db: db_dependency):
    print("*|" * 50)
    print("create-post get method")
    if request.state.is_authenticated:
        user = db.query(User).filter(User.username == request.state.username).first()
        print(user.role)
        if user.role == 'admin' or user.role == 'author':
            context = {
                "request": request,
            }
            return templates.TemplateResponse("create_post.html", context)
        else:
            msg = "Please be informed BLOGCHE website is an experimental project, and only ones that their role is considered as an AUTHOR are able to submit an article, oopsy doopsy"
            context = {
                "request": request,
                "msg": msg,
            }
            return templates.TemplateResponse("create_post.html", context)

    if request.state.is_authenticated == False:
        msg = "Please be informed BLOGCHE website is an experimental project, and only ones that their role is considered as an AUTHOR are able to submit an article, oopsy doopsy "
        context = {
            "request": request,
            "msg": msg,
        }
        return templates.TemplateResponse("create_post.html", context)


@router.post("/post/create-post", response_class=HTMLResponse)
async def create_post(request: Request, title: Annotated[str, Form()], description: Annotated[str, Form()],
                      file: Annotated[UploadFile, File()], db: db_dependency):
    if request.state.is_authenticated:
        user = db.query(User).filter(User.username == request.state.username).first()
        if user.role == 'admin' or user.role == 'author':
            print(user.role)
            rand_str = ''.join(random.choice(ascii_letters) for _ in range(5))
            new_name = f"_{rand_str}.".join(file.filename.rsplit('.', 1))
            file_path = f"static/upload/post/{new_name}"
            splited_path = file_path.rsplit(".", 1)[-1]
            print(splited_path)
            file_type = splited_path[-1]

            try:
                contents = file.file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)
            except Exception:
                return {"message": "There was an error uploading the file"}
            finally:
                file.file.close()

            new_post = Post(
                title=title,
                description=description,
                user_id=user.id,
                timestamp=datetime.datetime.now(),
                image_url=file_path,
                image_url_type=file_type)

            db.add(new_post)
            db.commit()
            db.refresh(new_post)

            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        else:
            msg = "Please be informed BLOGCHE website is an experimental project, and only ones that their role is considered as an AUTHOR are able to submit an article, oopsy doopsy"
            context = {
                "request": request,
                "msg": msg,
            }
            return templates.TemplateResponse("create_post.html", context)
    else:
        msg = "Please be informed BLOGCHE website is an experimental project, and only ones that their role is considered as an AUTHOR are able to submit an article, oopsy doopsy"
        context = {
            "request": request,
            "msg": msg,
        }
        return templates.TemplateResponse("create_post.html", context)

