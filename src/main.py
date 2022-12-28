import json
import operator
import urllib

from fastapi import FastAPI, Request, HTTPException
from peewee import *

config = json.load(open("./config.json", "r"))

app = FastAPI()

db = PostgresqlDatabase(None)

db_name = config["DATABASE"]
db_host = config["PGHOST"]
db_user = config["USER"]
db_password = config["PASSWORD"]

db.init(db_name, host=db_host, user=db_user, password=db_password)

if db.connect():
    print("Database connection established")


class BaseModel(Model):
    class Meta:
        database = db


def query_to_filters(raw_query_string: str):
    query_string = urllib.parse.unquote(raw_query_string, encoding="utf-8")
    query_list = query_string.split("&")
    if query_list[0] == "":
        return []

    operators = {
        "lt": operator.lt,
        "le": operator.le,
        "eq": operator.eq,
        "ge": operator.ge,
        "gt": operator.gt,
    }

    filters = []
    for item in query_list:
        field, value = item.split("=")
        if field in ["page", "sort", "limit", "fields"]:
            break
        op = "eq"
        if ("[" in field) and ("]" in field):
            field, op = field.split("[")
            op = op[:-1]

        filters.append({"field": field, "value": value, "op": operators[op]})

    return filters


################################
# Beers


class Beer(BaseModel):
    id = BigAutoField(index=True, primary_key=True)
    name = CharField(60)
    style = CharField(50, null=True)
    abv = DecimalField(3, 1, constraints=[Check("abv>=0")])
    price = DecimalField(6, 2, constraints=[Check("price>0")])

    class Meta:
        table_name = "beers"


@app.get("/beers/")
def get_beers(request: Request):
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

        res = {"qty": 0, "results": []}
        for beer in query.dicts():
            res["results"] += [beer]

        res["qty"] = len(res["results"])
        return res


@app.get("/beers/{beer_id}")
async def get_beer_by_id(beer_id):
    with db.atomic():
        query = Beer.select().where(Beer.id == beer_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            return query.get()


@app.post("/beers/")
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


@app.delete("/beers/{beer_id}")
async def delete_beer(beer_id):
    with db.atomic():
        query = Beer.select().where(Beer.id == beer_id)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Beer not found")
        else:
            return Beer.delete().where(Beer.id == beer_id).execute()
