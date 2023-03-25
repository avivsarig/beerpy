from peewee import *
from backend.database import db


class BaseModel(Model):
    class Meta:
        database = db


class Beer(BaseModel):
    id = BigAutoField(index=True, primary_key=True)
    name = CharField(60)
    style = CharField(50, null=True)
    abv = DecimalField(3, 1, constraints=[Check("abv>=0")])
    price = DecimalField(6, 2, constraints=[Check("price>0")])

    class Meta:
        table_name = "beers"


class User(BaseModel):
    id = BigAutoField(index=True, primary_key=True)
    name = CharField(60)
    email = CharField(60, unique=True)
    password = CharField(60)
    address = CharField(60, null=True)
    phone = CharField(12, null=True)

    class Meta:
        table_name = "users"


class Order(BaseModel):
    id = BigAutoField(index=True, primary_key=True)
    beer_id = ForeignKeyField(Beer)
    user_id = ForeignKeyField(User)
    qty = IntegerField()
    ordered_at = DateTimeField()
    price_paid = DecimalField(8, 2)

    class Meta:
        table_name = "orders"


class Stock(BaseModel):
    id = BigAutoField()
    beer_id = ForeignKeyField(Beer, unique=True)
    date_of_arrival = DateTimeField()
    qty_in_stock = IntegerField()

    class Meta:
        table_name = "stock"
