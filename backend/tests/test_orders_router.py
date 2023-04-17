from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *
import pytest

from backend.routers import orders
from backend.models import Order

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

def setup_module():
    db.bind([Order])
    db.create_tables([Order])

def teardown_module():
    db.drop_tables([Order])
    db.close()

def create_payload(beer_id=None, user_id=None, qty=None, ordered_at=None, price_paid=None):
    return {key: value for key, value in locals().items() if value is not None}

@pytest.fixture(scope="function")
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE orders RESTART IDENTITY CASCADE")
    yield