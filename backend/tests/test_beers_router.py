from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *
import pytest

from backend.routers import beers
from backend.models import Beer

from backend.tests.utils.payload_to_string import payload_to_string
from decimal import Decimal

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
        db.execute_sql("TRUNCATE TABLE beers RESTART IDENTITY CASCADE;")
    yield


class Test_create_beer:
    @pytest.mark.parametrize(
        "name, style, abv, price",
        [("test_beer1", None, 1.1, 1.11), ("test_beer2", "test_style2", 2.2, 2.22)],
    )
    def test_create_beer_content(self, clean_db, name, style, abv, price):
        payload = create_payload(name, style, abv, price)
        client.post("/beers/", json=payload)
        query = {
            key: float(value) if isinstance(value, Decimal) else value
            for key, value in Beer.select(Beer.name, Beer.style, Beer.abv, Beer.price)
            .where(Beer.name == name).dicts().get().items()
        }
        
        payload_with_none = payload
        for key in query.keys():
            if key not in payload.keys():
                payload_with_none[key] = None

        assert payload_with_none == query

    def test_create_ok_code(self, clean_db):
        response = client.post(
            "/beers/", json=create_payload("test_create_ok", "test_style", 1.1, 1.11)
        )
        assert response.status_code == 201

    @pytest.mark.parametrize(
        "name, style, abv, price",
        [
            (None, "test_style1", 5.0, 10.99),
            ("test_beer2", "test_style2", None, 14.99),
            ("test_beer3", "test_style3", 4.0, None),
        ],
    )
    def test_create_error_code(self,clean_db, name, style, abv, price):
        response = client.post("/beers/", json=create_payload(name, style, abv, price))
        assert response.status_code == 400

    def test_create_fail_invalid_abv(self, clean_db):
        response = client.post("/beers/", json=create_payload(
            "test_fail_abv",
            "test_style",
            -0.1,
            14.66
        ))
        assert response.status_code == 400

    def test_create_fail_invalid_price(self,clean_db):
        response = client.post("/beers/", json=create_payload(
            "test_fail_price",
            "test_style",
            1.0,
            -1.11
        ))
        assert response.status_code == 400


class Test_delete_beer:
    def test_delete(self,clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO beers (name, style, abv, price) VALUES ('test_delete', 'test_style', 5.0, 5.55) RETURNING id;"
            ).fetchall()[0][0]
        client.delete(f"/beers/{id}")
        assert (
            len(db.execute_sql(f"SELECT 1 FROM beers WHERE id = {id}").fetchall()) == 0
        )

    def test_delete_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql("INSERT INTO beers (name, style, abv, price) VALUES ('test_delete', 'test_style', 5.0, 5.55) RETURNING id;").fetchall()[0][0]
        response = client.delete(f"/beers/{id}")
        assert response.status_code == 204

    def test_delete_not_found(self):
        response = client.delete("/beers/1")
        assert response.status_code == 404


class Test_get_beer:
    def test_get_by_id(self, clean_db):
        data = create_payload(
            "test_get_by_id",
            "test_style",
            5.0,
            10.99
        )
        data_string = payload_to_string(data)
        with db.atomic():
            id = db.execute_sql(f"INSERT INTO beers (name, style, abv, price) VALUES ({data_string}) RETURNING id;").fetchall()[0][0]
        
        response = client.get(f"/beers/{id}")

        res_correct = data
        res_correct["id"] = id
        assert response.json()["__data__"] == res_correct

#     def test_get_ok_code(self):
#         assert 1 == 1

#     def test_get_not_found(self):
#         assert 1 == 1


# class Test_get_all_beers:
#     def test_get_all(self):
#         assert 1 == 1

#     def test_get_all_ok_code(self):
#         assert 1 == 1


# class Test_update_beer:
#     def test_update_content(self):
#         assert 1 == 1

#     def test_update_ok_code(self):
#         assert 1 == 1

#     def test_update_not_found(self):
#         assert 1 == 1

#     def test_update_invalid(self):
#         assert 1 == 1
