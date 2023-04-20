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


def setup_module():
    db.bind([Beer, User, Order])
    db.create_tables([Beer, User, Order])


def teardown_module():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE beers RESTART IDENTITY CASCADE;")
        db.execute_sql("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
    db.drop_tables([Order, User, Beer])
    db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_data():
    beers = []
    users = []

    for i in range(1, 6):
        beer = Beer.create(name=f"Test Beer {i}", style=f"Test Style {i}", abv=i, price=i)
        beers.append(beer)

        user = User.create(name=f"Test User {i}", email=f"test{i}@email.com", password=f"password{i}", address=f"{i} Main St", phone=f"123456789{i}")
        users.append(user)

    yield {"beers": beers, "users": users}


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE orders RESTART IDENTITY CASCADE;")
    yield

class Test_create_order:
    def test_create_order_content(self):
        payload = create_payload(1,1, 10, datetime.now().isoformat(), 10)
        response = client.post("/orders/", json=payload)
        query = Order.select(Order.beer_id, Order.user_id, Order.qty, Order.ordered_at, Order.price_paid).dicts().get()

        print(query)
        assert 1 == 0