from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *

import pytest
import random
import pytz
from datetime import datetime, timedelta

from backend.routers import stock
from backend.models import Stock, Beer

from backend.tests.utils.payload_to_string import payload_to_string
from backend.tests.utils.apply_filter import apply_filter
from decimal import Decimal

app = FastAPI()
app.include_router(stock.router)

db = PostgresqlDatabase(
    "test_beerpy",
    user="test_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)


def create_payload(beer_id=None, date_of_arrival=None, qty_in_stock=None):
    return {key: value for key, value in locals().items() if value is not None}


def string_to_datetime(date_str: str, strip_tz: bool = False):
    if strip_tz:
        dt = datetime.fromisoformat(date_str).replace(tzinfo=None)
    else:
        dt = datetime.fromisoformat(date_str)
    return dt


def setup_module():
    db.bind([Beer, Stock])
    db.create_tables([Beer, Stock])


def teardown_module():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE beers RESTART IDENTITY CASCADE;")
    db.drop_tables([Stock, Beer])
    db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_data():
    beers = []

    for i in range(1, 6):
        beer = Beer.create(
            name=f"Test Beer {i}", style=f"Test Style {i}", abv=i, price=i
        )
        beers.append(beer)

    yield {"beers": beers}


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE stock RESTART IDENTITY CASCADE;")
    yield


class Test_stock_router:
    def test_create_stock_content(self):
        payload = create_payload(
            beer_id=random.randint(1, 5),
            date_of_arrival=datetime.now().isoformat(),
            qty_in_stock=random.randint(0, 100),
        )
        response = client.post("/stock/", json=payload)

        query = (
            Stock.select(
                Stock.beer_id,
                Stock.date_of_arrival,
                Stock.qty_in_stock,
            )
            .dicts()
            .get()
        )
        query["date_of_arrival"] = query["date_of_arrival"].isoformat()

        assert query == payload

    def test_create_stock_ok_code(self):
        payload = create_payload(
            beer_id=random.randint(1, 5),
            date_of_arrival=datetime.now().isoformat(),
            qty_in_stock=random.randint(0, 100),
        )
        response = client.post("/stock/", json=payload)

        assert response.status_code == 201

    @pytest.mark.parametrize(
        "beer_id, date_of_arrival, qty_in_stock",
        [
            # Missing fields
            (None, datetime.now().isoformat(), 1),
            (1, None, 1),
            (1, datetime.now().isoformat(), None),
            # Non-existing foreign key
            (99, datetime.now().isoformat(), 1),
            # Invalid qty_in_stock
            (1, datetime.now().isoformat(), -1),
            (1, datetime.now().isoformat(), 10.5),
        ],
    )
    def test_create_stock_invalid_qty_in_stock(
        self, beer_id, date_of_arrival, qty_in_stock
    ):
        payload = create_payload(
            beer_id=beer_id, date_of_arrival=date_of_arrival, qty_in_stock=qty_in_stock
        )
        response = client.post("/stock/", json=payload)

        assert response.status_code == 400

    def test_create_stock_timezone_handling(self):
        time_utc = datetime.now(pytz.utc).isoformat()
        time_pdt = datetime.now(pytz.timezone("America/Los_Angeles")).isoformat()

        payload_utc = create_payload(1, time_utc, 1000)
        payload_pdt = create_payload(2, time_pdt, 100)

        response_utc = client.post("/stock/", json=payload_utc)
        response_pdt = client.post("/stock/", json=payload_pdt)

        query_utc = Stock.select().where(Stock.beer_id == 1).get()
        query_pdt = Stock.select().where(Stock.beer_id == 2).get()

        assert query_utc.date_of_arrival == query_utc.date_of_arrival
        assert query_pdt.date_of_arrival == query_pdt.date_of_arrival

    @pytest.mark.parametrize(
        "date_of_arrival",
        [
            "2020-02-29T00:00:00",  # Leap year date
            "2021-02-28T23:59:59",  # Non-leap year date
            "2023-03-12T02:00:00",  # Start of Daylight Saving Time in the US
            "2023-11-05T02:00:00",  # End of Daylight Saving Time in the US
        ],
    )
    def test_create_stock_edge_case_dates(self, date_of_arrival):
        payload = create_payload(1, date_of_arrival, 1000)
        response = client.post("/stock/", json=payload)

        query = Stock.select().where(Stock.beer_id == 1).get()
        arrival_datetime = string_to_datetime(date_of_arrival)

        assert query.date_of_arrival == arrival_datetime


class Test_delete_stock:
    def test_delete_stock_content(self):
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO stock (beer_id, date_of_arrival, qty_in_stock) VALUES ({random.randint(1, 5)}, '{datetime.now().isoformat()}',1000) RETURNING id;"
            ).fetchall()[0][0]
        client.delete(f"/stock/{id}")
        assert len(db.execute_sql("SELECT * FROM stock;").fetchall()) == 0

    def test_delete_stock_ok_code(self):
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO stock (beer_id, date_of_arrival, qty_in_stock) VALUES ({random.randint(1, 5)}, '{datetime.now().isoformat()}',1000) RETURNING id;"
            ).fetchall()[0][0]
        response = client.delete(f"/stock/{id}")
        assert response.status_code == 204

    def test_delete_stock_not_found(self):
        response = client.delete(f"/stock/1")
        assert response.status_code == 404


class Test_update_stock:
    @pytest.mark.parametrize(
            "beer_id, date_of_arrival, qty_in_stock",
            [
                (2, None, None),
                (None, "2022-02-01T00:00:00", None),
                (None, None, 2000),
            ]
    )
    def test_update_stock_content(self, beer_id, date_of_arrival, qty_in_stock):
        with db.atomic():
            time = "2022-01-01T00:00:00"
            id = db.execute_sql(
                f"INSERT INTO stock (beer_id, date_of_arrival, qty_in_stock) VALUES (1, '{time}',1000) RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(beer_id, date_of_arrival, qty_in_stock)

        old_stock = {
            key: value for key, value in Stock.select().where(Stock.id == id).dicts().get().items()
        }

        client.put(f"/stock/{id}", json=updated_payload)

        updated_stock = {
            key: value.isoformat()
            if isinstance(value, datetime)
            else value
            for key, value in Stock.select().where(Stock.id == id).dicts().get().items()
        }

        expected_res = updated_payload
        for key in old_stock.keys():
            if key not in expected_res.keys():
                if key == "date_of_arrival":
                    expected_res[key] = old_stock[key].isoformat()
                else:
                    expected_res[key] = old_stock[key]

        assert updated_stock == expected_res

    def test_update_stock_ok_code(self):
        with db.atomic():
            time = datetime.now().isoformat()
            id = db.execute_sql(
                f"INSERT INTO stock (beer_id, date_of_arrival, qty_in_stock) VALUES (1, '{time}',1000) RETURNING id;"
            ).fetchall()[0][0]


        updated_time = (datetime.fromisoformat(time) - timedelta(days=3)).isoformat()
        updated_payload = create_payload(2, updated_time, 2000)
        
        response = client.put(f"/stock/{id}", json=updated_payload)
        assert response.status_code == 200

    def test_update_stock_not_found(self):
        updated_payload = create_payload(2, datetime.now().isoformat(), 2000)
        
        response = client.put(f"/stock/1", json=updated_payload)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "beer_id, date_of_arrival, qty_in_stock",
        [
            # Non-existing foreign key
            (99, None, None),
            # Invalid qty_in_stock
            (None, None, -1),
            (None, None, 10.5),
        ],
    )
    def test_update_stock_invalid(self, beer_id, date_of_arrival, qty_in_stock):
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO stock (beer_id, date_of_arrival, qty_in_stock) VALUES (1, '{datetime.now().isoformat()}',1000) RETURNING id;"
            ).fetchall()[0][0]
        
        payload = create_payload(beer_id, date_of_arrival, qty_in_stock)
        response = client.put(f"/stock/{id}", json=payload)

        assert response.status_code == 400


# class Test_get_stock:
#     def test_get_stock_content(self):
#         assert 1==0

#     def test_get_stock_ok_code(self):
#         assert 1==0

#     def test_get_stock_not_found(self):
#         assert 1==0


# class Test_get_all_stock:
#     def test_get_all_stock_content(self):
#         assert 1==0

#     def test_get_all_stock_ok_code(self):
#         assert 1==0


# class Test_filter_stock:
#     def test_get_all_filter_stock(self):
#         assert 1==0

#     def test_get_all_multi_filter_stock(self):
#         assert 1==0
