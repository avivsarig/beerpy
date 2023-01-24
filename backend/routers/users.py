from fastapi import APIRouter, HTTPException, Request, Response
from peewee_dir.peewee import IntegrityError
from database import db
from models import User

from utils.query_to_filters import query_to_filters

router = APIRouter(prefix="/users", responses={404: {"description": "Not found"}})

@router.get("/")
async def get_users(request: Request):
    query = User.select(User.id, User.name, User.address, User.phone)
    filters = query_to_filters(request["query_string"])
    if filters != []:

        for filter in filters:
            if filter["field"] == "name":
                query = query.where(User.name == filter["value"])
            if filter["field"] == "email":
                query = query.where(User.email == filter["value"])
            if filter["field"] == "address":
                query = query.where(User.address == filter["value"])
            if filter["field"] == "phone":
                query = query.where(User.phone == filter["value"])

    res: dict = {"qty": 0, "results": []}
    for user in query.dicts():
        res["results"] += [user]

    res["qty"] = len(res["results"])
    return res

@router.get('/{user_id}')
async def get_user_by_id(user_id):
    query = User.select(User.id, User.name, User.address, User.phone)
    if not query.exists():
        raise HTTPException(status_code=404, detail ='User not found')
    else:
        return query.get()