from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *
import pytest

from backend.routers import users
from backend.models import User

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


def create_payload(name=None, email=None, password=None, address=None, phone=None):
    return {key: value for key, value in locals().items() if value is not None}


def payload_to_string(data):
    return ", ".join(["'{}'".format(s) for s in list(data.values())])


@pytest.fixture(scope="function")
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
    yield


class Test_create_user:
    @pytest.mark.parametrize(
        "name, email, password, address, phone",
        [
            ("test_user1", "test_email1", "test_password1", None, "test_phone1"),
            ("test_user2", "test_email2", "test_password2", "test_address2", None),
        ],
    )
    def test_create_user_content(self, clean_db, name, email, password, address, phone):
        payload = create_payload(name, email, password, address, phone)
        response = client.post("/users/", json=payload)

        query = User.select().where(User.name == "name").dicts()
        assert query == payload

    def test_create_user_ok_code(self, clean_db):
        response = client.post(
            "/users/",
            json=create_payload(
                "test_user", "test_email", "test_password", "test_address", "test_phone"
            ),
        )
        assert response.status_code == 201

    @pytest.mark.parametrize(
        "name, email, password",
        [
            (None, "test_email1", "test_password"),
            ("test_user", None, "test_password"),
            ("test_user", "test_email3", None),
        ],
    )
    def test_create_user_error_code(self, clean_db, name, email, password):
        response = client.post("/users/", json=create_payload(name, email, password))
        assert response.status_code == 400

    def test_create_duplicate_email(self, clean_db):
        with db.atomic():
            db.execute_sql(
                "INSERT INTO users (name, email, password) VALUES ('test_create_duplicate_email1', 'test_duplicate_email', 'test_pw1');"
            )
        response = client.post(
            "/users/",
            json=create_payload(
                "test_create_duplicate_email2", "test_duplicate_email", "test_password2"
            ),
        )
        assert response.status_code == 400


class Test_delete_user:
    def test_delete(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_delete', 'test_email', 'test_pw', 'test_address', 'test_phone') RETURNING id;"
            ).fetchall()[0][0]
        client.delete(f"/users/{id}")
        assert (
            len(db.execute_sql(f"SELECT 1 FROM users WHERE id = {id}").fetchall()) == 0
        )

    def test_delete_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_delete_ok_code', 'test_email', 'test_pw', 'test_address', 'test_phone') RETURNING id;"
            ).fetchall()[0][0]
        response = client.delete(f"/users/{id}")
        assert response.status_code == 204

    def test_delete_not_found(self, clean_db):
        response = client.delete("/users/1")
        assert response.status_code == 404


class Test_get_user:
    def test_get_by_id(self, clean_db):
        data = create_payload(
            "test_get_by_id", "test_email", "test_pw", "test_address", "test_phone"
        )
        data_string = payload_to_string(data)
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO users (name, email, password, address, phone) VALUES ({data_string}) RETURNING id;"
            ).fetchall()[0][0]
        response = client.get(f"/users/{id}")
        res_correct = {
            key: data[key] for key in ["name", "email", "address", "phone"]
        }
        res_correct["id"] = id
        assert response.json()["__data__"] == res_correct

    def test_get_by_id_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_get_by_id_ok_code', 'test_email', 'test_pw', 'test_address', 'test_phone') RETURNING id;"
            ).fetchall()[0][0]
        response = client.get(f"/users/{id}")
        assert response.status_code == 200

    def test_get_by_id_not_found(self, clean_db):
        response = client.get("/users/1")
        assert response.status_code == 404


class Test_get_all:
    def test_get_all(self, clean_db):
        with db.atomic():
            for i in range(10):
                data = create_payload(f'test_get_all{i}', f'test_email{i}', f'test_pw{i}', f'test_address{i}', f'test_phone{i}')
                data_string = payload_to_string(data)
                db.execute_sql(f"INSERT INTO users (name, email, password, address, phone) VALUES ({data_string});")

        response = client.get("/users/")
        print(response.json()['results'])
        assert False