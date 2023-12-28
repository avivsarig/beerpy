from typing import Type, List

from fastapi import Depends, HTTPException, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import DeclarativeMeta

from backend.database import get_db

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error


async def get_all(
    model: DeclarativeMeta,
    schema: Type,
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
