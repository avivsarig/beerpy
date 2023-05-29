from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend import models, schemas, settings

from backend.utils.query_to_filters import query_to_filters
from backend.utils.error_handler import response_from_error


router = APIRouter(prefix="/orders")


@router.get("/", response_model=list[schemas.Order])
async def get_orders(request: Request):
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

    res: dict = {"qty": 0, "results": []}
    for order in query.dicts():
        res["results"] += [order]

    res["qty"] = len(res["results"])
    return res


@router.get("/{order_id}")
async def get_order_by_id(order_id):
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


@router.post("/")
async def create_order(request: Request):
    body = await request.json()
    with db.atomic():
        try:
            res = Order.create(**body)
            return res
        except IntegrityError as e:
            print(e, flush=True)
            return Response()


@router.delete("/{order_id}")
async def delete_order(order_id):
    try:
        query = Order.select().where(Order.id == order_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Order not found")
        else:
            with db.atomic():
                return Order.delete().where(Order.id == order_id).execute()

    except IntegrityError as e:
        print(e, flush=True)
        return Response()


@router.put("/{order_id}")
async def update(request: Request, order_id):
    body = await request.json()
    try:
        query = Order.select().where(Order.id == order_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Order not found")
        else:
            with db.atomic():
                Order.update(**body).where(Order.id == order_id).execute()

    except IntegrityError as e:
        print(e, flush=True)
        return Response()
