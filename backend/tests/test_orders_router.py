from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *

import pytest
import pytz
from datetime import datetime

from backend.routers import orders
from backend.models import Order, Beer, User

from backend.tests.utils.payload_to_string import payload_to_string

app = FastAPI()
app.include_router(orders.router)

db = PostgresqlDatabase(
    "test_beerpy",
    user="test_user",
    password="iLoveTesting",
    host="localhost",
    port=5432,
)

client = TestClient(app)


def create_payload(
    beer_id=None, user_id=None, qty=None, ordered_at=None, price_paid=None
):
    return {key: value for key, value in locals().items() if value is not None}


def setup_module():
    db.bind([Beer, User, Order])
    db.create_tables([Beer, User, Order])


def teardown_module():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE beers RESTART IDENTITY CASCADE;")
        db.execute_sql("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
    db.drop_tables([Order, User, Beer])
    db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_data():
    beers = []
    users = []

    for i in range(1, 6):
        beer = Beer.create(
            name=f"Test Beer {i}", style=f"Test Style {i}", abv=i, price=i
        )
        beers.append(beer)

        user = User.create(
            name=f"Test User {i}",
            email=f"test{i}@email.com",
            password=f"password{i}",
            address=f"{i} Main St",
            phone=f"123456789{i}",
        )
        users.append(user)

    yield {"beers": beers, "users": users}


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    with db.atomic():
        db.rollback()
        db.execute_sql("TRUNCATE TABLE orders RESTART IDENTITY CASCADE;")
    yield


def string_to_datetime(date_str: str, strip_tz: bool = False):
    if strip_tz:
        dt = datetime.fromisoformat(date_str).replace(tzinfo=None)
    else:
        dt = datetime.fromisoformat(date_str)
    return dt


class Test_create_order:
    def test_create_order_content(self):
        time = datetime.now().isoformat()
        payload = create_payload(1, 1, 10, time, 10)
        response = client.post("/orders/", json=payload)
        query = (
            Order.select(
                Order.beer_id,
                Order.user_id,
                Order.qty,
                Order.ordered_at,
                Order.price_paid,
            )
            .dicts()
            .get()
        )
        query["price_paid"] = float(query["price_paid"])
        query["ordered_at"] = query["ordered_at"].isoformat()

        assert query == payload

    def test_create_order_ok_code(self):
        response = client.post(
            "/orders/", json=create_payload(1, 1, 10, datetime.now().isoformat(), 10)
        )

        assert response.status_code == 201

    @pytest.mark.parametrize(
        "beer_id, user_id, qty, ordered_at, price_paid",
        [
            # Missing required fields
            (None, 1, 10, "2023-04-30T17:12:24.485793", 10),
            (1, None, 10, "2023-04-30T17:12:24.485793", 10),
            (1, 1, None, "2023-04-30T17:12:24.485793", 10),
            # Non-existent foreign keys
            (999, 1, 10, "2023-04-30T17:12:24.485793", 10),
            (1, 999, 10, "2023-04-30T17:12:24.485793", 10),
        ],
    )
    def test_create_order_error_code(
        self, beer_id, user_id, qty, ordered_at, price_paid
    ):
        payload = create_payload(beer_id, user_id, qty, ordered_at, price_paid)
        response = client.post("/orders/", json=payload)

        print(response.status_code, response.json())
        assert response.status_code == 400

    def test_create_order_timezone_handling(self):
        time_utc = datetime.now(pytz.utc).isoformat()
        time_pdt = datetime.now(pytz.timezone("America/Los_Angeles")).isoformat()

        payload_utc = create_payload(1, 1, 10, time_utc, 10)
        payload_pdt = create_payload(2, 2, 10, time_pdt, 10)

        response_utc = client.post("/orders/", json=payload_utc)
        response_pdt = client.post("/orders/", json=payload_pdt)

        query_utc = Order.select().where(Order.user_id == 1).get()
        query_pdt = Order.select().where(Order.user_id == 2).get()

        utc_time = string_to_datetime(time_utc, strip_tz=True)
        pdt_time = string_to_datetime(time_pdt, strip_tz=True)

        assert query_utc.ordered_at == utc_time
        assert query_pdt.ordered_at == pdt_time

    @pytest.mark.parametrize(
        "ordered_at",
        [
            "2020-02-29T00:00:00",  # Leap year date
            "2021-02-28T23:59:59",  # Non-leap year date
            "2023-03-12T02:00:00",  # Start of Daylight Saving Time in the US
            "2023-11-05T02:00:00",  # End of Daylight Saving Time in the US
        ],
    )
    def test_create_order_edge_case_dates(self, ordered_at):
        payload = create_payload(1, 1, 10, ordered_at, 10)
        response = client.post("/orders/", json=payload)

        query = Order.select().where(Order.user_id == 1).get()
        ordered_at_datetime = string_to_datetime(ordered_at)

        assert query.ordered_at == ordered_at_datetime


class Test_delete_order:
    def test_delete_order(self):
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO orders (beer_id, user_id, qty, ordered_at, price_paid) VALUES (1, 1, 10, '{datetime.now().isoformat()}', 10) RETURNING id;"
            ).fetchall()[0][0]
        client.delete(f"/orders/{id}")
        assert len(db.execute_sql("SELECT * FROM orders;").fetchall()) == 0


    def test_delete_ok_code(self):
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO orders (beer_id, user_id, qty, ordered_at, price_paid) VALUES (1, 1, 10, '{datetime.now().isoformat()}', 10) RETURNING id;"
            ).fetchall()[0][0]
        response = client.delete(f"/orders/{id}")
        assert response.status_code == 204

    def test_delete_not_found(self):
        response = client.delete(f"/orders/1")
        assert response.status_code == 404

class Test_get_order:
    def test_get_by_id(self):
        time = datetime.now().isoformat()
        data = create_payload(1, 1, 10, time, 10)
        data_string = payload_to_string(data)
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO orders (user_id, beer_id, qty, ordered_at, price_paid) VALUES ({data_string}) RETURNING id;"
            ).fetchall()[0][0]
        data["id"] = id

        response = client.get(f"/orders/{id}")

        assert response.json()['__data__'] == data

    def test_get_by_id_ok_code(self):
        with db.atomic():
            id = db.execute_sql(
                f"INSERT INTO orders (user_id, beer_id, qty, ordered_at, price_paid) VALUES (1, 1, 10, '{datetime.now().isoformat()}', 10) RETURNING id;"
            ).fetchall()[0][0]
        response = client.get(f"/orders/{id}")
        assert response.status_code == 200

    def test_get_by_id_not_found(self):
        response = client.get(f"/orders/1")
        assert response.status_code == 404

# class Test_get_all:
#     def test_get_all(self):
#         assert 1==0

#     def test_get_all_ok_code(self):
#         assert 1==0

# class Test_filter_orders:
#     def test_get_all_orders_with_filter(self):
#         assert 1==0

#     def test_get_all_multi_filter(self):
#         assert 1==0

#     def test_get_all_orders_with_filter_ok_code(self):
#         assert 1==0

# class Test_update_order:
#     def test_update_order_content(self):
#         assert 1==0

#     def test_update_order_ok_code(self):
#         assert 1==0

#     def test_update_order_not_found(self):
#         assert 1==0

#     def test_order_invalid(self):
#         assert 1==0
