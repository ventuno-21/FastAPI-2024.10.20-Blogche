from typing import Annotated
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends

engine = create_engine("sqlite:///blogche.db", connect_args={'check_same_thread': False})
Base = declarative_base()

localsession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = localsession()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
