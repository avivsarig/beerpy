from fastapi import APIRouter, HTTPException, Request, Response
from peewee import IntegrityError
from database import db
from models import Beer

# from urllib.error import HTTPError

from utils.query_to_filters import query_to_filters


router = APIRouter(prefix="/beers", responses={404: {"description": "Not found"}})


@router.get("/")
async def get_beers(request: Request):
    query = Beer.select()
    filters = query_to_filters(request["query_string"])
    if filters != []:
        for filter in filters:
            if filter["field"] == "name":
                query = query.where(Beer.name == filter["value"])
            if filter["field"] == "style":
                query = query.where(Beer.style == filter["value"])
            if filter["field"] == "abv":
                query = query.where(filter["op"](Beer.abv, filter["value"]))
            if filter["field"] == "price":
                query = query.where(filter["op"](Beer.price, filter["value"]))

    res: dict = {"qty": 0, "results": []}
    for beer in query.dicts():
        res["results"] += [beer]

    res["qty"] = len(res["results"])
    return res


@router.get("/{beer_id}")
async def get_beer_by_id(beer_id):
    query = Beer.select().where(Beer.id == beer_id)
    if not query.exists():
        raise HTTPException(status_code=404, detail="Beer not found")
    else:
        return query.get()


@router.post("/")
async def create_beer(request: Request):
    body = await request.json()
    try:
        with db.atomic():
            res = Beer.create(**body)
            return res
    except IntegrityError as e:
        print(e, flush=True)
        return Response()


@router.delete("/{beer_id}")
async def delete_beer(beer_id):
    with db.atomic():
        query = Beer.select().where(Beer.id == beer_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            return Beer.delete().where(Beer.id == beer_id).execute()


@router.put("/{beer_id}")
async def update_beer(request: Request, beer_id):
    body = await request.json()
    try:
        query = Beer.select().where(Beer.id == beer_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            with db.atomic():
                Beer.update(**body).where(Beer.id == beer_id).execute()

    except IntegrityError as e:
        print(e, flush=True)
        return Response()
