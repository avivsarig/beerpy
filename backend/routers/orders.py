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

PAGE_LIMIT = int(os.getenv("ORDERS_PAGE_LIMIT", settings.BEER_PAGE_LIMIT))

router = APIRouter(prefix="/orders")


@router.get("/", response_model=list[schemas.Order])
async def get_orders(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    return await get_all(models.Order, request, db, skip, limit)


@router.get("/{order_id}", response_model=schemas.Order)
async def get_order_by_id(order_id: int, db: Session = Depends(get_db)):
    return await get_one(models.Order, order_id, db, "order_id")


@router.post("/", response_model=schemas.Order, status_code=201)
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return await create_one(models.Order, order, db)


@router.delete("/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    return await delete_one(models.Order, order_id, db, "order_id")


@router.put("/{order_id}", response_model=schemas.Order)
async def update(order_id: int, order: schemas.Order, db: Session = Depends(get_db)):
    return await update_one(models.Order, order, order_id, db, "order_id")
