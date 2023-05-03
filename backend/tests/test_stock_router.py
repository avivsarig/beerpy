from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *

import pytest
import random
import pytz
from datetime import datetime, timedelta

from backend.routers import stock
from backend.models import Stock, Beer

from backend.tests.utils.payload_to_string import payload_to_string
from backend.tests.utils.apply_filter import apply_filter
from decimal import Decimal

app = FastAPI()
app.include_router(stock.router)

db = PostgresqlDatabase(
    "test_beerpy",
    user="test_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)

def create_payload(
            beer_id=None,
            date_of_arrival=None,
            qty_in_stock=None
        ):
    return {key: value for key, value in locals().items() if value is not None}

def setup_module():
    db.bind([Beer, Stock])
    db.create_tables([Beer, Stock])

def teardown_module():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE beers RESTART IDENTITY CASCADE;")
    db.drop_tables([Stock, Beer])
    db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_data():
    beers = []

    for i in range(1, 6):
        beer = Beer.create(
            name=f"Test Beer {i}", style=f"Test Style {i}", abv=i, price=i
        )
        beers.append(beer)

    yield {"beers": beers}


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE stock RESTART IDENTITY CASCADE;")
    yield

