import os

from fastapi import APIRouter, Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend import models, schemas, settings

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error
from backend.routers.handler_factory import get_all, get_one


PAGE_LIMIT = int(os.getenv("STOCK_PAGE_LIMIT", settings.STOCK_PAGE_LIMIT))

router = APIRouter(prefix="/stock")


@router.get("/", response_model=list[schemas.Stock])
async def get_stock(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.Stock, schemas.Stock, request, db, skip, limit)


@router.get("/{stock_id}", response_model=schemas.Stock)
async def get_stock_by_id(stock_id: int, db: Session = Depends(get_db)):
    return await get_one(models.Stock, schemas.Stock, stock_id, db, "stock_id")


@router.post("/", response_model=schemas.Stock, status_code=201)
async def create_stock(stock: schemas.Stock, db: Session = Depends(get_db)):
    try:
        db_stock = models.Stock(**stock.dict())
        db.add(db_stock)
        db.commit()
        db.refresh(db_stock)
        return db_stock

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.delete("/{stock_id}")
async def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    try:
        db_stock = (
            db.query(models.Stock).filter(models.Stock.stock_id == stock_id).first()
        )
        if db_stock is None:
            raise HTTPException(status_code=404, detail="Stock not found\n")
        db.delete(db_stock)
        db.commit()
        return Response(status_code=204)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.put("/{stock_id}", response_model=schemas.Stock)
async def update_stock(
    stock_id: int, stock: schemas.Stock, db: Session = Depends(get_db)
):
    try:
        db_stock = (
            db.query(models.Stock).filter(models.Stock.stock_id == stock_id).first()
        )
        if db_stock is None:
            raise HTTPException(status_code=404, detail="Stock not found\n")
        for attr, value in stock.dict().items():
            if value is not None:
                setattr(stock, attr, value)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)
