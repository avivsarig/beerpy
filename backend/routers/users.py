import os

from fastapi import APIRouter, Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend import models, schemas, settings

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error
from backend.routers.handler_factory import get_all, get_one, create_one

PAGE_LIMIT = int(os.getenv("USER_PAGE_LIMIT", settings.USER_PAGE_LIMIT))

router = APIRouter(prefix="/users")


@router.get("/", response_model=list[schemas.User])
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.User, schemas.User, request, db, skip, limit)


@router.get("/{user_id}")
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return await get_one(models.User, schemas.User, user_id, db, "user_id")


@router.post("/", response_model=schemas.User, status_code=201)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return await create_one(models.User, schemas.UserCreate, db)


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found\n")
        db.delete(db_user)
        db.commit()
        return Response(status_code=204)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user: schemas.User, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found\n")
        for attr, value in user.dict().items():
            if value is None:
                setattr(user, attr, value)

            db.commit()
            db.refresh(db_user)
            return user

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)
