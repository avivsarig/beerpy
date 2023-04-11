from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *
import pytest

from backend.routers import beers
from backend.models import Beer

from backend.tests.utils.payload_to_string import payload_to_string

app = FastAPI()
app.include_router(beers.router)

db = PostgresqlDatabase(
    "test_beerpy",
    user="test_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)


def setup_module():
    db.bind([Beer])
    db.create_tables([Beer])


def teardown_module():
    db.drop_tables([Beer])
    db.close()


def create_payload(name=None, style=None, abv=None, price=None):
    return {key: value for key, value in locals().items() if value is not None}


@pytest.fixture(scope="function")
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
    yield
