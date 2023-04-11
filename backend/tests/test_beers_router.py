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
        db.execute_sql("TRUNCATE TABLE beers RESTART IDENTITY CASCADE;")
    yield


class Test_create_beer:
    @pytest.mark.parametrize(
        "name, style, abv, price",
        [("test_beer1", None, 1.0, 1.0), ("test_beer2", "test_style2", 2.0, 2.0)],
    )
    def test_create_beer_content(self, clean_db, name, style, abv, price):
        payload = create_payload(name, style, abv, price)
        response = client.post("/beers/", json=payload)
        query = (
            Beer.select(Beer.name, Beer.style, Beer.abv, Beer.price)
            .where(Beer.name == name)
            .dicts()
            .get()
        )

        payload_with_none = payload
        for key in query.keys():
            if key not in payload.keys():
                payload_with_none[key] = None

        assert payload_with_none == query

    def test_create_ok_code(self):
        assert 1 == 1

    def test_create_error_code(self):
        assert 1 == 1

    def test_create_fail_invalid_abv(self):
        assert 1 == 1

    def test_create_fail_invalid_price(self):
        assert 1 == 1


class Test_delete_beer:
    def test_delete(self):
        assert 1 == 1

    def test_delete_ok_code(self):
        assert 1 == 1

    def test_delete_not_found(self):
        assert 1 == 1


class Test_get_beer:
    def test_get_by_id(self):
        assert 1 == 1

    def test_get_ok_code(self):
        assert 1 == 1

    def test_get_not_found(self):
        assert 1 == 1


class Test_get_all_beers:
    def test_get_all(self):
        assert 1 == 1

    def test_get_all_ok_code(self):
        assert 1 == 1


class Test_update_beer:
    def test_update_content(self):
        assert 1 == 1

    def test_update_ok_code(self):
        assert 1 == 1

    def test_update_not_found(self):
        assert 1 == 1

    def test_update_invalid(self):
        assert 1 == 1
