from fastapi import APIRouter, HTTPException, Request, Response
from peewee import IntegrityError
from backend.database import db
from backend.models import Stock

from backend.utils.error_handler import response_from_error
from backend.utils.query_to_filters import query_to_filters

router = APIRouter(prefix="/stock")


@router.get("/")
async def get_stock(request: Request):
    query = Stock.select()
    filters = query_to_filters(request["query_string"])
    if filters != []:
        for filter in filters:
            if filter["field"] == "beer_id":
                query = query.where(Stock.beer_id == filter["value"])
            if filter["field"] == "date_of_arrival":
                query = query.where(
                    filter["op"](Stock.date_of_arrival, filter["value"])
                )
            if filter["field"] == "qty_in_stock":
                query = query.where(filter["op"](Stock.qty_in_stock, filter["value"]))

    res: dict = {"qty": 0, "results": []}
    for stock in query.dicts():
        res["results"] += [stock]

    res["qty"] = len(res["results"])
    return res


@router.get("/{stock_id}")
async def get_stock_by_id(stock_id):
    query = Stock.select().where(Stock.id == stock_id)
    if not query.exists():
        raise HTTPException(status_code=404, detail="Stock not found")
    else:
        return query.get()


@router.post("/")
async def create_stock(request: Request):
    body = await request.json()
    try:
        with db.atomic():
            res = Stock.create(**body)
            return Response(status_code=201)
    except IntegrityError as e:
        print(e, flush=True)
        return Response()


@router.delete("/{stock_id}")
async def delete_stock(stock_id):
    query = Stock.select().where(Stock.id == stock_id)
    if not query.exists():
        raise HTTPException(status_code=404, detail="Stock not found")
    else:
        with db.atomic():
            Stock.delete().where(Stock.id == stock_id).execute()
            return Response(status_code=204)


@router.put("/{stock_id}")
async def update_stock(request: Request, stock_id: int):
    body = await request.json()
    try:
        query = Stock.select().where(Stock.id == stock_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Stock not found")
        else:
            with db.atomic():
                Stock.update(**body).where(Stock.id == stock_id).execute()
    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)
