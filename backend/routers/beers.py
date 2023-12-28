import os

from fastapi import APIRouter, Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend import models, schemas, settings

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error
from backend.routers.handler_factory import get_all

PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", settings.BEER_PAGE_LIMIT))

router = APIRouter(prefix="/beers")


@router.get("/", response_model=list[schemas.Beer])
async def get_beers(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.Beer, schemas.Beer, request, db, skip, limit)


@router.get("/{beer_id}", response_model=schemas.Beer)
async def get_beer_by_id(beer_id: int, db: Session = Depends(get_db)):
    try:
        db_beer = db.query(models.Beer).filter(models.Beer.beer_id == beer_id).first()
        if db_beer is None:
            raise HTTPException(status_code=404, detail="Beer not found\n")
        return db_beer

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.post("/", response_model=schemas.Beer, status_code=201)
async def create_beer(beer: schemas.BeerCreate, db: Session = Depends(get_db)):
    try:
        db_beer = models.Beer(**beer.dict())
        db.add(db_beer)
        db.commit()
        db.refresh(db_beer)
        return db_beer

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.delete("/{beer_id}")
async def delete_beer(beer_id: int, db: Session = Depends(get_db)):
    try:
        db_beer = db.query(models.Beer).filter(models.Beer.beer_id == beer_id).first()
        if db_beer is None:
            raise HTTPException(status_code=404, detail="Beer not found\n")
        db.delete(db_beer)
        db.commit()
        return Response(status_code=204)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.put("/{beer_id}", response_model=schemas.Beer)
async def update_beer(beer_id: int, beer: schemas.Beer, db: Session = Depends(get_db)):
    try:
        db_beer = db.query(models.Beer).filter(models.Beer.beer_id == beer_id).first()
        if db_beer is None:
            raise HTTPException(status_code=404, detail="Beer not found\n")
        for attr, value in beer.dict().items():
            if value is not None:
                setattr(beer, attr, value)

            db.commit()
            return beer

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)
