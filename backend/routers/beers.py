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

PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", settings.BEER_PAGE_LIMIT))

router = APIRouter(prefix="/beers")


@router.get("/", response_model=list[schemas.Beer])
async def get_beers(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.Beer, request, db, skip, limit)


@router.get("/{beer_id}", response_model=schemas.Beer)
async def get_beer_by_id(beer_id: int, db: Session = Depends(get_db)):
    return await get_one(models.Beer, beer_id, db, "beer_id")


@router.post("/", response_model=schemas.Beer, status_code=201)
async def create_beer(beer: schemas.BeerCreate, db: Session = Depends(get_db)):
    return await create_one(models.Beer, beer, db)


@router.delete("/{beer_id}")
async def delete_beer(beer_id: int, db: Session = Depends(get_db)):
    return await delete_one(models.Beer, beer_id, db, "beer_id")


@router.put("/{beer_id}", response_model=schemas.Beer)
async def update_beer(beer_id: int, beer: schemas.Beer, db: Session = Depends(get_db)):
    return await update_one(models.Beer, beer, beer_id, db, "beer_id")
