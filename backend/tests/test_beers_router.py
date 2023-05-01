from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *

import pytest
import random

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
            .where(Beer.name == name)
            .dicts()
            .get()
            .items()
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
    def test_create_error_code(self, clean_db, name, style, abv, price):
        response = client.post("/beers/", json=create_payload(name, style, abv, price))
        assert response.status_code == 400

    def test_create_fail_invalid_abv(self, clean_db):
        response = client.post(
            "/beers/", json=create_payload("test_fail_abv", "test_style", -0.1, 14.66)
        )
        assert response.status_code == 400

    def test_create_fail_invalid_price(self, clean_db):
        response = client.post(
            "/beers/", json=create_payload("test_fail_price", "test_style", 1.0, -1.11)
        )
        assert response.status_code == 400


class Test_delete_beer:
    def test_delete(self, clean_db):
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
            id = db.execute_sql(
                "INSERT INTO beers (name, style, abv, price) VALUES ('test_delete', 'test_style', 5.0, 5.55) RETURNING id;"
            ).fetchall()[0][0]
        response = client.delete(f"/beers/{id}")
        assert response.status_code == 204

    def test_delete_not_found(self):
        response = client.delete("/beers/1")
        assert response.status_code == 404


class Test_get_beer:
    def test_get_by_id(self, clean_db):
        data = create_payload("test_get_by_id", "test_style", 5.0, 10.99)
        data_string = payload_to_string(data)
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO beers (name, style, abv, price) VALUES ({data_string}) RETURNING id;"
            ).fetchall()[0][0]

        response = client.get(f"/beers/{id}")

        res_correct = data
        res_correct["id"] = id
        assert response.json()["__data__"] == res_correct

    def test_get_by_id_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO beers (name, style, abv, price) VALUES ('test_delete', 'test_style', 5.0, 5.55) RETURNING id;"
            ).fetchall()[0][0]
        response = client.get(f"/beers/{id}")
        assert response.status_code == 200

    def test_delete_not_found(self, clean_db):
        response = client.get("/beers/1")
        assert response.status_code == 404


class Test_get_all_beers:
    def test_get_all(self, clean_db):
        with db.atomic():
            for i in range(10):
                data = create_payload(
                    f"test_get_all{i}",
                    f"test_style{i}",
                    round(random.uniform(0, 20), 1),
                    round(random.uniform(0, 100), 1),
                )
                data_string = payload_to_string(data)
                db.execute_sql(
                    f"INSERT INTO beers (name, style, abv, price) VALUES ({data_string});"
                )

        response = client.get("/beers/")
        assert response.json()["qty"] == 10

        query = Beer.select().dicts()
        for beer_dict, response_dict in zip(query, response.json()["results"]):
            beer_dict = {
                key: float(value) if isinstance(value, Decimal) else value
                for key, value in beer_dict.items()
            }
            for attr in ["name", "style", "abv", "price"]:
                assert beer_dict[attr] == response_dict[attr]
        assert len(Beer.select()) == len(response.json()["results"])

    def test_get_all_ok_code(self, clean_db):
        with db.atomic():
            for i in range(10):
                data = create_payload(
                    f"test_get_all{i}",
                    f"test_style{i}",
                    round(random.uniform(0, 20), 1),
                    round(random.uniform(0, 100), 1),
                )
                data_string = payload_to_string(data)
                db.execute_sql(
                    f"INSERT INTO beers (name, style, abv, price) VALUES ({data_string});"
                )

        response = client.get("/beers/")
        assert response.status_code == 200


class Test_filter_beers:
    @pytest.mark.parametrize(
        "field, op, value, expected_qty",
        [
            ("name", "", "test_get_all_filter1", 1),
            ("style", "", "test_style2", 1),
            ("abv", "[lt]", 3, 2),
            ("abv", "[le]", 3, 3),
            ("abv", "[eq]", 3, 1),
            ("abv", "[ge]", 7, 3),
            ("abv", "[gt]", 7, 2),
            ("price", "[lt]", 5, 4),
            ("price", "[le]", 5, 5),
            ("price", "[eq]", 5, 1),
            ("price", "[ge]", 5, 5),
            ("price", "[gt]", 5, 4),
            ("not_a_field", "", "non_existent_value", 9),
        ],
    )
    def test_get_all_beers_filter(self, clean_db, field, op, value, expected_qty):
        data_list = []
        for i in range(1, 10):
            data = create_payload(
                name=f"test_get_all_filter{i}",
                style=f"test_style{i}",
                abv=i,
                price=i,
            )
            data_list.append(payload_to_string(data))
        data_string = f"({'),('.join(data_list)})"

        with db.atomic():
            db.execute_sql(
                f"INSERT INTO beers (name, style, abv, price) VALUES {data_string}"
            )

        url = f"/beers/?{field}{op}={value}"
        response = client.get(url)
        assert response.json()["qty"] == expected_qty
        if expected_qty == 1:
            assert response.json()["results"][0][field] == value

    def test_get_all_multi_filter(self, clean_db):
        data_list = []
        for i in range(1, 10):
            data = create_payload(
                name=f"test_get_all_filter{i}",
                style=f"test_style{i}",
                abv=i,
                price=i,
            )
            data_list.append(payload_to_string(data))
        data_string = f"({'),('.join(data_list)})"

        with db.atomic():
            db.execute_sql(
                f"INSERT INTO beers (name, style, abv, price) VALUES {data_string}"
            )

        url = f"/beers/?abv[lt]=5&price[ge]=3"
        response = client.get(url)
        assert response.json()["qty"] == 2


class Test_update_beer:
    @pytest.mark.parametrize(
        "name, style, abv, price",
        [
            ("test_beer1", None, None, None),
            (None, "test_style2", None, None),
            (None, None, 4.0, None),
            (None, None, None, 14.99),
        ],
    )
    def test_update_content(self, clean_db, name, style, abv, price):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO beers (name, style, abv, price) VALUES ('test_update', 'test_style', 5.0, 13.99) RETURNING id"
            ).fetchall()[0][0]

        updated_payload = create_payload(name, style, abv, price)

        old_beer = {
            key: float(value) if isinstance(value, Decimal) else value
            for key, value in Beer.select().where(Beer.id == id).dicts().get().items()
        }
        client.put(f"/beers/{id}", json=updated_payload)
        query = {
            key: float(value) if isinstance(value, Decimal) else value
            for key, value in Beer.select().where(Beer.id == id).dicts().get().items()
        }

        expected_res = updated_payload
        for key in old_beer.keys():
            if key not in expected_res.keys():
                expected_res[key] = old_beer[key]

        assert query == updated_payload

    def test_update_ok_code(self, clean_db):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO beers (name, style, abv, price) VALUES ('test_update', 'test_style', 5.0, 13.99) RETURNING id"
            ).fetchall()[0][0]

        updated_payload = create_payload(
            name="updated_test_user",
            style="updated_test_style",
            abv=6.6,
            price=22.22,
        )
        response = client.put(f"/beers/{id}", json=updated_payload)

        assert response.status_code == 200

    def test_update_not_found(self, clean_db):
        non_existent_id = 1
        updated_payload = create_payload(
            name="updated_test_user",
            style="updated_test_style",
            abv=6.6,
            price=22.22,
        )
        response = client.put(f"/beers/{non_existent_id}", json=updated_payload)

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "abv, price",
        [
            (-15.0, None),
            (None, -10.11),
        ],
    )
    def test_update_invalid(self, clean_db, abv, price):
        with db.atomic():
            id = db.execute_sql(
                "INSERT INTO beers (name, style, abv, price) VALUES ('test_update', 'test_style', 5.0, 13.99) RETURNING id"
            ).fetchall()[0][0]
        updated_payload = create_payload(name=None, style=None, abv=abv, price=price)
        response = client.put(f"/beers/{id}", json=updated_payload)

        assert response.status_code == 400
