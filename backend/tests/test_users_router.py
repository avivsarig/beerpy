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
        res_correct = {key: data[key] for key in ["name", "email", "address", "phone"]}
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
                data = create_payload(
                    f"test_get_all{i}",
                    f"test_email{i}",
                    f"test_pw{i}",
                    f"test_address{i}",
                    f"test_phone{i}",
                )
                data_string = payload_to_string(data)
                db.execute_sql(
                    f"INSERT INTO users (name, email, password, address, phone) VALUES ({data_string});"
                )

        query = User.select(User.id, User.name, User.email, User.address, User.phone)
        response = client.get("/users/")
        assert response.json()["qty"] == 10

        for user_dict, response_dict in zip(query.dicts(), response.json()["results"]):
            for attr in ["id", "name", "email", "address", "phone"]:
                assert (
                    user_dict[attr] == response_dict[attr]
                ), f"{attr} incorrect"
        assert len(query) == len(response.json()["results"])

    def test_get_all_ok_code(self, clean_db):
        response = client.get("/users/")
        assert response.status_code == 200


class Test_update_user:
    def test_update_user_content(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_update', 'test_email', 'test_pw', 'test_address', 'test_phone') RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(
            name="updated_test_user",
            email="updated_test_email",
            password="updated_test_pw",
            address="updated_test_address",
            phone="updated_test_phone",
        )
        response = client.put(f"/users/{id}", json=updated_payload)

        query = User.select().where(User.id == id).dicts()
        assert query == updated_payload

    def test_update_user_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_update_ok_code', 'test_email', 'test_pw', 'test_address', 'test_phone') RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(
            name="updated_test_user",
            email="updated_test_email",
            password="updated_test_pw",
            address="updated_test_address",
            phone="updated_test_phone",
        )
        response = client.put(f"/users/{id}", json=updated_payload)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "name, email, password",
        [
            (None, "updated_test_email", "updated_test_pw"),
            ("updated_test_user", None, "updated_test_pw"),
            ("updated_test_user", "updated_test_email", None),
        ],
    )
    def test_update_user_error_code(self, clean_db, name, email, password):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_update_error_code', 'test_email', 'test_pw', 'test_address', 'test_phone') RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(name, email, password)
        response = client.put(f"/users/{id}", json=updated_payload)

        assert response.status_code == 400

    def test_update_user_not_found(self, clean_db):
        non_existent_id = 1
        updated_payload = create_payload(
            name="updated_test_user",
            email="updated_test_email",
            password="updated_test_pw",
            address="updated_test_address",
            phone="updated_test_phone",
        )
        response = client.put(f"/users/{non_existent_id}", json=updated_payload)

        assert response.status_code == 404


class Test_filter_users:
    def test_get_all_with_filter(self, clean_db):
        with db.atomic():
            for i in range(10):
                data = create_payload(
                    f"test_get_all_filter{i}",
                    f"test_email{i}",
                    f"test_pw{i}",
                    f"test_address{i}",
                    f"test_phone{i}",
                )
                data_string = payload_to_string(data)
                db.execute_sql(
                    f"INSERT INTO users (name, email, password, address, phone) VALUES ({data_string});"
                )


            response = client.get("/users/", params={"name": "test_get_all_filter2"})

            assert len(response.json()["results"]) == 1
            assert (
                response.json()["results"][0]["__data__"]["name"]
                == "test_get_all_filter2"
            )

    def test_get_all_with_filter_ok_code(self, clean_db):
        response = client.get("/users/", params={"name": "test_get_all_filter_ok_code"})
        assert response.status_code == 200
