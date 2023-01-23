from fastapi import APIRouter, HTTPException, Request, Response
<<<<<<< HEAD:backend/routers/users.py
from peewee import IntegrityError
=======
from peewee_dir.peewee import IntegrityError
>>>>>>> 8aafe6e (created users.py file in routers folder, added the router to main.py):routers/users.py
from database import db
from models import User

from utils.query_to_filters import query_to_filters

<<<<<<< HEAD:backend/routers/users.py
router = APIRouter(prefix="/users", responses={404: {"description": "Not found\n"}})


@router.get("/")
async def get_users(request: Request) -> dict:
    query = User.select(User.id, User.name, User.address, User.phone)
    filters = query_to_filters(request["query_string"])
    if filters != []:
        for filter in filters:
            if filter["field"] == "name":
                query = query.where(User.name == filter["value"])
            elif filter["field"] == "email":
                query = query.where(User.email == filter["value"])
            elif filter["field"] == "address":
                query = query.where(User.address == filter["value"])
            elif filter["field"] == "phone":
                query = query.where(User.phone == filter["value"])

    res: dict = {"qty": 0, "results": []}
    for user in query.dicts():
        res["results"] += [user]

    res["qty"] = len(res["results"])
    return res


@router.get("/{user_id}")
async def get_user_by_id(user_id):
    query = User.select(User.id, User.name, User.address, User.phone)
    if not query.exists():
        raise HTTPException(status_code=404, detail="User not found\n")
    else:
        return query.get()


@router.post("/")
async def create_user(request: Request):
    body = await request.json()
    try:
        with db.atomic():
            res = User.create(**body)
            return res
    except IntegrityError as e:
        print(e, flush=True)
        return Response()


@router.delete("/{user_id}")
async def delete_user(user_id):
    query = User.select().where(User.id == user_id)
    if not query.exists():
        raise HTTPException(status_code=404, detail="User not found\n")
    else:
        with db.atomic():
            return User.delete().where(User.id == user_id).execute()


@router.put("/{user_id}")
async def update_user(request: Request, user_id):
    body = await request.json()
    try:
        query = User.select().where(User.id == user_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="User not found\n")
        else:
            with db.atomic():
                User.update(**body).where(User.id == user_id).execute()
    except IntegrityError as e:
        print(e, flush=True)
        return Response()
=======
router = APIRouter(prefix="/users", responses={404: {"description": "Not found"}})
>>>>>>> 8aafe6e (created users.py file in routers folder, added the router to main.py):routers/users.py
