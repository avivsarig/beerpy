from fastapi import APIRouter, HTTPException, Request
from database import db
from models import Order, Beer, User

from utils.query_to_filters import query_to_filters


router = APIRouter(prefix="/orders", responses={404: {"description": "Not found"}})


class Results:
    qty = int
    results = list


@router.get("/")
async def get_orders(request: Request):
    with db.atomic():
        query = Order.select()
        filters = query_to_filters(request["query_string"])
        if filters != []:
            for filter in filters:
                if filter["field"] == "beer_id":
                    query = query.where(Order.beer_id == filter["beer_id"])
                if filter["field"] == "user_id":
                    query = query.where(Order.user_id == filter["user_id"])
                if filter["field"] == "qty":
                    query = query.where(filter["op"](Order.qty, filter["value"]))
                if filter["field"] == "ordered_at":
                    query = query.where(filter["op"](Order.ordered_at, filter["value"]))
                if filter["field"] == "price_paid":
                    query = query.where(filter["op"](Order.price_paid, filter["value"]))

        res = {"qty": 0, "results": []}
        for order in query.dicts():
            res["results"] += [order]

        res["qty"] = len(res["results"])
        return res


@router.get("/{order_id}")
async def get_order_by_id(order_id):
    with db.atomic():
        query = (
            Order.select(
                Order.id,
                Beer.name,
                User.name,
                Order.qty,
                Order.ordered_at,
                Order.price_paid,
            )
            .join(Beer, on=(Order.beer_id == Beer.id))
            .join(User, on=(Order.user_id == User.id))
            .where(Order.id == order_id)
        )

        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            return query.get()