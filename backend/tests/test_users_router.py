from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *
import pytest

from backend.routers import users
from backend.models import User

from backend.tests.utils.payload_to_string import payload_to_string

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
            ("test_user1", "test_email1", "test_password1", None, "+972-555-555-5551"),
            ("test_user2", "test_email2", "test_password2", "test_address2", None),
        ],
    )
    def test_create_user_content(self, clean_db, name, email, password, address, phone):
        payload = create_payload(name, email, password, address, phone)
        response = client.post("/users/", json=payload)
        query = (
            User.select(User.name, User.email, User.address, User.phone)
            .where(User.name == name)
            .dicts()
            .get()
        )

        payload_with_none = payload
        payload_with_none.pop("password")
        for key in query.keys():
            if key not in payload.keys():
                payload_with_none[key] = None
        assert payload_with_none == query

    def test_create_user_ok_code(self, clean_db):
        response = client.post(
            "/users/",
            json=create_payload(
                "test_user",
                "test_email",
                "test_password",
                "test_address",
                "+972-555-555-555",
            ),
        )
        assert response.status_code == 201

    @pytest.mark.parametrize(
        "name, email, password",
        [
            (None, "test_email1", "test_password1"),
            ("test_user2", None, "test_password2"),
            ("test_user3", "test_email3", None),
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
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_delete', 'test_email', 'test_pw', 'test_address', '+972-555-555-555') RETURNING id;"
            ).fetchall()[0][0]
        client.delete(f"/users/{id}")
        assert (
            len(db.execute_sql(f"SELECT 1 FROM users WHERE id = {id}").fetchall()) == 0
        )

    def test_delete_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_delete_ok_code', 'test_email', 'test_pw', 'test_address', '+972-555-555-555') RETURNING id;"
            ).fetchall()[0][0]
        response = client.delete(f"/users/{id}")
        assert response.status_code == 204

    def test_delete_not_found(self, clean_db):
        response = client.delete("/users/1")
        assert response.status_code == 404


class Test_get_user:
    def test_get_by_id(self, clean_db):
        data = create_payload(
            "test_get_by_id",
            "test_email",
            "test_pw",
            "test_address",
            "+972-555-555-555",
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
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_get_by_id_ok_code', 'test_email', 'test_pw', 'test_address', '+972-555-555-555') RETURNING id;"
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
                    f"+972-555-555-555{i}",
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
                assert user_dict[attr] == response_dict[attr]
        assert len(query) == len(response.json()["results"])

    def test_get_all_ok_code(self, clean_db):
        response = client.get("/users/")
        assert response.status_code == 200


class Test_update_user:
    @pytest.mark.parametrize(
        "name,email,password,address,phone",
        [
            ("updated_test_name", None, None, None, None),
            (None, "updated_test_email", None, None, None),
            (None, None, "updated_test_password", None, None),
            (None, None, None, "updated_test_address", None),
            (None, None, None, None, "+972-555-555-666"),
            (
                "test_name",
                "test_email",
                "test_password",
                "test_address",
                "+972-555-555-666",
            ),
        ],
    )
    def test_update_user_content(self, clean_db, name, email, password, address, phone):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_update', 'test_email', 'test_pw', 'test_address', '+972-555-555-555') RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(name, email, password, address, phone)

        old_user = User.select().where(User.id == id).dicts().get()
        client.put(f"/users/{id}", json=updated_payload)
        query = User.select().where(User.id == id).dicts().get()

        expected_res = updated_payload
        for key in old_user.keys():
            if key not in expected_res.keys():
                expected_res[key] = old_user[key]

        assert query == expected_res

    def test_update_user_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO users (name, email, password, address, phone) VALUES ('test_update_ok_code', 'test_email', 'test_pw', 'test_address', '+972-555-555-555') RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(
            name="updated_test_user",
            email="updated_test_email",
            password="updated_test_pw",
            address="updated_test_address",
            phone="+972-555-555-666",
        )
        response = client.put(f"/users/{id}", json=updated_payload)

        assert response.status_code == 200

    def test_update_user_not_found(self, clean_db):
        non_existent_id = 1
        updated_payload = create_payload(
            name="updated_test_user",
            email="updated_test_email",
            password="updated_test_pw",
            address="updated_test_address",
            phone="+972-555-555-666",
        )
        response = client.put(f"/users/{non_existent_id}", json=updated_payload)

        assert response.status_code == 404

class Test_filter_users:
    @pytest.mark.parametrize(
        "field, value, expected_qty",
        [
        ("name", "test_get_all_filter1", 1),
        ("email", "test_email2", 1),
        ("address", "test_address3", 1),
        ("phone", "+972-555-555-5554", 1),
        ("Knock_knock", "test_get_all_filter5", 9),
        ("email", "whos_there", 0),
        ])
    def test_get_all_users_with_filter(self, clean_db, field, value, expected_qty):
        data_list = []
        for i in range(1,10):
            data = create_payload(
                f"test_get_all_filter{i}",
                f"test_email{i}",
                f"test_pw{i}",
                f"test_address{i}",
                f"+972-555-555-555{i}",
            )
            data_list.append(payload_to_string(data))
        data_string = f"({'),('.join(data_list)})"

        with db.atomic():
            db.execute_sql(
                f"INSERT INTO users (name, email, password, address, phone) VALUES {data_string};"
            )

        url = f"/users/?{field}={value}"
        response = client.get(url)
        
        print(response.json())
        assert response.json()["qty"] == expected_qty
        if expected_qty == 1:
            assert (    
                response.json()["results"][0][field]
                == value
            )

    def test_get_all_users_with_filter_ok_code(self, clean_db):
        response = client.get("/users/", params={"name": "test_get_all_filter_ok_code"})
        assert response.status_code == 200
