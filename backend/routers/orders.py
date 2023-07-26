import os

from fastapi import APIRouter, Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend import models, schemas, settings

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error

PAGE_LIMIT = int(os.getenv("ORDERS_PAGE_LIMIT", settings.BEER_PAGE_LIMIT))

router = APIRouter(prefix="/orders")


@router.get("/", response_model=list[schemas.Order])
async def get_orders(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = PAGE_LIMIT,
):
    try:
        raw_query_string = str(request.url.query)
        filters = query_to_filters(raw_query_string)

        query = db.query(models.Order)
        for f in filters:
            column = getattr(models.Order, f["field"], None)
            if column:
                query = query.filter(f["op"](column, f["value"]))

        orders = query.offset(skip).limit(limit).all()
        return orders

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.get("/{order_id}", response_model=schemas.Order)
async def get_order_by_id(order_id: int, db: Session = Depends(get_db)):
    try:
        db_order = (
            db.query(models.Order).filter(models.Order.order_id == order_id).first()
        )
        if db_order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return db_order

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.post("/", response_model=schemas.Order, status_code=201)
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        db_order = models.Order(**order.dict())
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.delete("/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        db_order = (
            db.query(models.Order).filter(models.Order.order_id == order_id).first()
        )
        if db_order is None:
            raise HTTPException(status_code=404, detail="Order not found\n")
        db.delete(db_order)
        db.commit()
        return Response(status_code=204)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.put("/{order_id}", response_model=schemas.Order)
async def update(order_id: int, order: schemas.Order, db: Session = Depends(get_db)):
    try:
        db_order = (
            db.query(models.Order).filter(models.Order.order_id == order_id).first()
        )
        if db_order is None:
            raise HTTPException(status_code=404, detail="Order not found\n")
        for attr, value in order.dict().items():
            if value is not None:
                setattr(order, attr, value)

            db.commit()
            return order

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)
