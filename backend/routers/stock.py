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


PAGE_LIMIT = int(os.getenv("STOCK_PAGE_LIMIT", settings.STOCK_PAGE_LIMIT))

router = APIRouter(prefix="/stock")


@router.get("/", response_model=list[schemas.Stock])
async def get_stock(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.Stock, request, db, skip, limit)


@router.get("/{stock_id}", response_model=schemas.Stock)
async def get_stock_by_id(stock_id: int, db: Session = Depends(get_db)):
    return await get_one(models.Stock, stock_id, db, "stock_id")


@router.post("/", response_model=schemas.Stock, status_code=201)
async def create_stock(stock: schemas.Stock, db: Session = Depends(get_db)):
    return await create_one(models.Stock, stock, db)


@router.delete("/{stock_id}")
async def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    return await delete_one(models.Stock, stock_id, db, "stock_id")


@router.put("/{stock_id}", response_model=schemas.Stock)
async def update_stock(
    stock_id: int, stock: schemas.Stock, db: Session = Depends(get_db)
):
    return await update_one(models.Stock, stock, stock_id, db, "stock_id")
