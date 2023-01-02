from fastapi import APIRouter, HTTPException, Request
from database import db
from models import Beer

from typing_extensions import TypedDict

from utils.query_to_filters import query_to_filters


router = APIRouter(prefix="/beers", responses={404: {"description": "Not found"}})

Results = TypedDict("Results", {"qty": int, "results": list})


@router.get("/")
async def get_beers(request: Request):
    with db.atomic():
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

        res: Results = {"qty": 0, "results": []}
        for beer in query.dicts():
            res["results"] += [beer]

        res["qty"] = len(res["results"])
        return res


@router.get("/{beer_id}")
async def get_beer_by_id(beer_id):
    with db.atomic():
        query = Beer.select().where(Beer.id == beer_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            return query.get()


@router.post("/")
async def create_beer(request: Request):
    body = await request.json()
    with db.atomic():
        try:
            res = Beer.create(**body)
            return res
        except:
            raise HTTPException(
                status_code=400,
                detail="A beer must have a name, A positive ABV and a positive Value. Try again.",
            )


@router.delete("/{beer_id}")
async def delete_beer(beer_id):
    with db.atomic():
        query = Beer.select().where(Beer.id == beer_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            return Beer.delete().where(Beer.id == beer_id).execute()
