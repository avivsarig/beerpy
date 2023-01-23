from fastapi import APIRouter, HTTPException, Request, Response
from peewee_dir.peewee import IntegrityError
from database import db
from models import User

from utils.query_to_filters import query_to_filters

router = APIRouter(prefix="/users", responses={404: {"description": "Not found"}})
