from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import PostgresqlDatabase, IntegrityError
import pytest

from routers import users
from models import User

app = FastAPI()
app.include_router(users.router)

db = PostgresqlDatabase(
    "test_beerpy",
    user="test_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)

def setup_module():
    db.bind([User])
    db.create_tables([User])

def teardown_module():
    db.drop_tables([User])
    db.close()

def create_user(name=None, email=None, password=None, address=None, phone=None):
    payload = {key: value for key, value in locals().items() if value is not None}

    return client.post("/users/", json=payload)

def test_create_response():
    response = create_user("test_user", "test_email", "test_password")

    assert response.status_code == 200
    assert response.json()['__data__'] == {
        "id": 1,
        "name": "test_user",
        "email": "test_email",
        "password": "test_password",
    }