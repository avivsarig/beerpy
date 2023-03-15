from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import PostgresqlDatabase, IntegrityError
import pytest

from ..routers import users
from ..models import User

app = FastAPI()
app.include_router(users.router)

db = PostgresqlDatabase(
    "test_db",
    user="testing_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)


def setup_module():
    db.bind([User])
    db.create_tables([User])
    print("DB is up.")


def teardown_module():
    db.drop_tables([User])
    db.close()
    print("DB is down.")


class TestCreateUser:
    def create_user(name=None, email=None, password=None, address=None, phone=None):
        payload = {key: value for key, value in locals().items() if value is not None}

        return client.post("/", json=payload)

    def test_create_response():
        response = self.create_user("test_user", "test_email", "test_password")

        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "name": "test_user",
            "email": "test_email",
            "password": "test_password",
        }
