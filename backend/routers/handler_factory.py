from pydantic import BaseModel
from typing import Type, List

from fastapi import Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import DeclarativeMeta

from backend.database import get_db

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error


async def get_all(
    model: Type[DeclarativeMeta],
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
) -> List:
    try:
        raw_query_string = str(request.url.query)
        filters = query_to_filters(raw_query_string)

        query = db.query(model)
        for filter in filters:
            column = getattr(model, filter["field"], None)
            if column:
                query = query.filter(filter["op"](column, filter["value"]))

        items = query.offset(skip).limit(limit).all()
        return items

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


async def get_one(
    model: Type[DeclarativeMeta],
    item_id: int,
    db: Session = Depends(get_db),
    id_field: str = "id",
):
    try:
        db_item = db.query(model).filter(getattr(model, id_field) == item_id).first()
        if db_item is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found\n")
        return db_item

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


async def create_one(
    model: Type[DeclarativeMeta],
    schema: BaseModel,
    db: Session = Depends(get_db),
):
    try:
        db_item = model(**schema.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


async def delete_one(
    model: Type[DeclarativeMeta],
    item_id: int,
    db: Session = Depends(get_db),
    id_field: str = "id",
):
    try:
        db_item = db.query(model).filter(getattr(model, id_field) == item_id).first()
        if db_item is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found\n")
        db.delete(db_item)
        db.commit()
        return Response(status_code=204)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


async def update_one(
    model: Type[DeclarativeMeta],
    schema: BaseModel,
    item_id: int,
    db: Session = Depends(get_db),
    id_field: str = "id",
):
    try:
        db_item = db.query(model).filter(getattr(model, id_field) == item_id).first()
        if db_item is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found\n")

        for attr, value in schema.model_dump().items():
            if value is not None:
                setattr(db_item, attr, value)

        db.commit()
        db.refresh(db_item)
        return db_item

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)
