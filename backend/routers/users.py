import os

from fastapi import APIRouter, Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend import models, schemas, settings

from backend.utils.error_handler import response_from_error
from backend.routers.handler_factory import (
    get_all,
    get_one,
    create_one,
    delete_one,
    update_one,
)

PAGE_LIMIT = int(os.getenv("USER_PAGE_LIMIT", settings.USER_PAGE_LIMIT))

router = APIRouter(prefix="/users")


@router.get("/", response_model=list[schemas.User])
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.User, request, db, skip, limit)


@router.get("/{user_id}")
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return await get_one(models.User, user_id, db, "user_id")


@router.post("/", response_model=schemas.User, status_code=201)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return await create_one(models.User, user, db)


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    return await delete_one(models.User, user_id, db, "user_id")


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user: schemas.User, db: Session = Depends(get_db)):
    return await update_one(models.User, user, user_id, db, "user_id")
