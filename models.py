from peewee_dir.peewee import *
from database import db


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
