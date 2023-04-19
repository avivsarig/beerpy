from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *

import pytest
from datetime import datetime

from backend.routers import orders
from backend.models import Order, Beer, User

from backend.tests.utils.payload_to_string import payload_to_string

app = FastAPI()
app.include_router(orders.router)

db = PostgresqlDatabase(
    "test_beerpy",
    user="test_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)

def create_payload(beer_id=None, user_id=None, qty=None, ordered_at=None, price_paid=None):
    return {key: value for key, value in locals().items() if value is not None}

@pytest.fixture(scope="module", autouse=True)
def setup_data():
    db.bind([Beer, User, Order])
    db.create_tables([Beer, User, Order])

    beers = []
    users = []

    for i in range(1, 6):
        beer = Beer.create(name=f"Test Beer {i}", style=f"Test Style {i}", abv=i, price=i)
        beers.append(beer)

        user = User.create(name=f"Test User {i}", email=f"test{i}@email.com", password=f"password{i}", address=f"{i} Main St", phone=f"123456789{i}")
        users.append(user)

    yield {"beers": beers, "users": users}

    db.drop_tables([User, Beer, Order])
    db.close()


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE orders RESTART IDENTITY CASCADE")
    yield

class Test_create_order:
    def test_create_order_content(self):
        payload = create_payload(1,1,10, datetime.now(), 10)
        assert 1 == 0