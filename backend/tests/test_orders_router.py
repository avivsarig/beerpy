from fastapi import FastAPI
from fastapi.testclient import TestClient
from peewee import *

import pytest
import random
import pytz
from datetime import datetime, timedelta

from backend.routers import orders
from backend.models import Order, Beer, User

from backend.tests.utils.payload_to_string import payload_to_string
from backend.tests.utils.apply_filter import apply_filter
from decimal import Decimal

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


def string_to_datetime(date_str: str, strip_tz: bool = False):
    if strip_tz:
        dt = datetime.fromisoformat(date_str).replace(tzinfo=None)
    else:
        dt = datetime.fromisoformat(date_str)
    return dt


def setup_module():
    db.bind([Item, User, Order])
    db.create_tables([Item, User, Order])


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

        assert query_utc.ordered_at == query_utc.ordered_at
        assert query_pdt.ordered_at == query_pdt.ordered_at

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

    def test_create_order_same_user(self):
        time = datetime.now().isoformat()
        for i in range(1, 3):
            payload = create_payload(i, 1, 10, time, 10)
            response = client.post("/orders/", json=payload)
        assert response.status_code == 201

    def test_create_order_same_beer(self):
        time = datetime.now().isoformat()
        for i in range(1, 3):
            payload = create_payload(1, i, 10, time, 10)
            response = client.post("/orders/", json=payload)
        assert response.status_code == 201


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

        assert response.json()["__data__"] == data

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


class Test_get_all:
    def test_get_all(self):
        with db.atomic():
            for i in range(1, 6):
                time = datetime.now().isoformat()
                data = create_payload(
                    i, i, random.randint(0, 50), time, random.uniform(0, 200)
                )

                data_string = payload_to_string(data)
                db.execute_sql(
                    f"INSERT INTO orders (user_id, beer_id, qty, ordered_at, price_paid) VALUES ({data_string}) RETURNING id;"
                )

        response = client.get("/orders/")
        assert response.json()["qty"] == 5

        query = Order.select().dicts()
        for order_dict, response_dict in zip(query, response.json()["results"]):
            order_dict = {
                key: float(value) if isinstance(value, Decimal) else value
                for key, value in order_dict.items()
            }
            for attr in ["user_id", "beer_id", "qty", "ordered_at", "price_paid"]:
                if attr == "ordered_at":
                    order_dict[attr] = order_dict[attr].isoformat()
                assert order_dict[attr] == response_dict[attr]
        assert len(Order.select()) == len(response.json()["results"])

    def test_get_all_ok_code(self):
        with db.atomic():
            for i in range(1, 6):
                time = datetime.now().isoformat()
                data = create_payload(
                    i, i, random.randint(0, 50), time, random.uniform(0, 200)
                )

                data_string = payload_to_string(data)
                db.execute_sql(
                    f"INSERT INTO orders (user_id, beer_id, qty, ordered_at, price_paid) VALUES ({data_string}) RETURNING id;"
                )

        response = client.get("/orders/")
        assert response.status_code == 200


class Test_filter_orders:
    @pytest.mark.parametrize(
        "field, op, value",
        [
            ("qty", "", 5),
            ("qty", "[lt]", 6),
            ("qty", "[le]", 7),
            ("qty", "[eq]", 8),
            ("qty", "[ge]", 3),
            ("qty", "[gt]", 2),
            ("ordered_at", "[lt]", "2023-01-01"),
            ("ordered_at", "[le]", "2023-02-01"),
            ("ordered_at", "[eq]", "2023-03-01"),
            ("ordered_at", "[ge]", "2023-04-01"),
            ("ordered_at", "[gt]", "2023-05-01"),
            ("price_paid", "", 50.00),
            ("price_paid", "[lt]", 100.00),
            ("price_paid", "[le]", 150.00),
            ("price_paid", "[eq]", 200.00),
            ("price_paid", "[ge]", 50.00),
            ("price_paid", "[gt]", 25.00),
            ("not_a_field", "", "non_existent_value"),
        ],
    )
    def test_get_all_orders_with_filter(self, field, op, value):
        data_list = []
        for _ in range(10):
            beer_id = random.randint(1, 5)
            user_id = random.randint(1, 5)
            qty = random.randint(1, 10)
            days_ago = random.randint(1, 1000)
            ordered_at = datetime.now() - timedelta(days=days_ago)
            price_paid = round(random.uniform(1, 200), 2)

            data = create_payload(beer_id, user_id, qty, ordered_at, price_paid)
            data_list.append(data)

        keys_order = ["beer_id", "user_id", "qty", "ordered_at", "price_paid"]
        data_string = (
            f"{'),('.join([payload_to_string(data, keys_order) for data in data_list])}"
        )

        with db.atomic():
            db.execute_sql(
                f"INSERT INTO orders (beer_id, user_id, qty, ordered_at, price_paid) VALUES ({data_string});"
            )

        if field == "ordered_at":
            value = datetime.strptime(value, "%Y-%m-%d")
        filtered_data = apply_filter(data_list, field, op, value)

        url = f"/orders/?{field}{op}={value}"
        response = client.get(url)
        response_data = response.json()["results"]

        for item in response_data:
            del item["id"]
            item["ordered_at"] = datetime.fromisoformat(item["ordered_at"])

        assert response_data == filtered_data

    def test_get_all_orders_with_multi_filter(self, clean_db):
        data_list = []
        for _ in range(10):
            beer_id = random.randint(1, 5)
            user_id = random.randint(1, 5)
            qty = random.randint(1, 10)
            days_ago = random.randint(1, 1000)
            ordered_at = datetime.now() - timedelta(days=days_ago)
            price_paid = round(random.uniform(1, 200), 2)

            data = create_payload(beer_id, user_id, qty, ordered_at, price_paid)
            data_list.append(data)

        keys_order = ["beer_id", "user_id", "qty", "ordered_at", "price_paid"]
        data_string = (
            f"{'),('.join([payload_to_string(data, keys_order) for data in data_list])}"
        )

        with db.atomic():
            db.execute_sql(
                f"INSERT INTO orders (beer_id, user_id, qty, ordered_at, price_paid) VALUES ({data_string});"
            )

        filter1_field, filter1_op, filter1_value = "qty", "[lt]", 5
        filter2_field, filter2_op, filter2_value = "price_paid", "[ge]", 50.00

        filtered_data = apply_filter(
            data_list, filter1_field, filter1_op, filter1_value
        )
        filtered_data = apply_filter(
            filtered_data, filter2_field, filter2_op, filter2_value
        )

        url = f"/orders/?{filter1_field}{filter1_op}={filter1_value}&{filter2_field}{filter2_op}={filter2_value}"
        response = client.get(url)
        response_data = response.json()["results"]

        for item in response_data:
            del item["id"]
            item["ordered_at"] = datetime.fromisoformat(item["ordered_at"])

        assert response_data == filtered_data


class Test_update_order:
    @pytest.mark.parametrize(
        "beer_id, user_id, qty, ordered_at, price_paid",
        [
            (2, None, None, None, None),
            (None, 2, None, None, None),
            (None, None, 2, None, None),
            (None, None, None, datetime.now().isoformat(), None),
            (None, None, None, None, 2),
            (2, 2, 2, datetime.now().isoformat(), 2),
        ],
    )
    def test_update_order_content(self, beer_id, user_id, qty, ordered_at, price_paid):
        with db.atomic():
            time = datetime.now()
            id = db.execute_sql(
                f"INSERT INTO orders (beer_id, user_id, qty, ordered_at, price_paid) VALUES (1, 1, 1, '{time}', 1) RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(beer_id, user_id, qty, ordered_at, price_paid)

        old_order = {
            key: float(value) if isinstance(value, Decimal) else value
            for key, value in Order.select().where(Order.id == id).dicts().get().items()
        }

        client.put(f"/orders/{id}", json=updated_payload)

        updated_order = {
            key: value.isoformat()
            if isinstance(value, datetime)
            else float(value)
            if isinstance(value, Decimal)
            else value
            for key, value in Order.select().where(Order.id == id).dicts().get().items()
        }

        expected_res = updated_payload
        for key in old_order.keys():
            if key not in expected_res.keys():
                if key == "ordered_at":
                    expected_res[key] = old_order[key].isoformat()
                elif key == "price_paid":
                    expected_res[key] = float(old_order[key])
                else:
                    expected_res[key] = old_order[key]

        assert updated_order == expected_res

    def test_update_order_ok_code(self):
        with db.atomic():
            time = datetime.now()
            id = db.execute_sql(
                f"INSERT INTO orders (beer_id, user_id, qty, ordered_at, price_paid) VALUES (1, 1, 1, '{time}', 1) RETURNING id;"
            ).fetchall()[0][0]

        updated_payload = create_payload(
            beer_id=2,
            user_id=2,
            qty=2,
            ordered_at=datetime.now().isoformat(),
            price_paid=2,
        )

        response = client.put(f"/orders/{id}", json=updated_payload)

        assert response.status_code == 200

    def test_update_order_not_found(self):
        updated_payload = create_payload(
            beer_id=2,
            user_id=2,
            qty=2,
            ordered_at=datetime.now().isoformat(),
            price_paid=2,
        )

        response = client.put(f"/orders/1", json=updated_payload)

        assert response.status_code == 404
