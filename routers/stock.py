from fastapi import APIRouter, HTTPException, Request, Response
from peewee_dir.peewee import IntegrityError
from database import db
from models import Stock

from utils.query_to_filters import query_to_filters

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
                query = query.where(filter["op"](Stock.date_of_arrival, filter["value"]))
            if filter["field"] == "qty_in_stock":
                query = query.where(filter["op"](Stock.qty_in_stock, filter["value"]))

    res: dict = {"qty": 0, "results": []}
    for stock in query.dicts():
        res["results"] += [stock]

    res["qty"] = len(res["results"])
    return res