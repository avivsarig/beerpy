import pytest
import random
import os

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import settings

from backend.main import app
from backend.database import Base, get_db
from backend.models import Beer as BeerModel

# TODO:
# from backend.schemas import Beer, BeerCreate

PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", settings.BEER_PAGE_LIMIT))

# Setup test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_database):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the get_db dependency with the test session
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def db_beer_rows_gen(qty: int):
    beers = []

    styles = [
        "IPA",
        "Stout",
        "Porter",
        "Pilsner",
        "Lager",
        "Wheat Beer",
        "Sour Ale",
        "Pale Ale",
        "Belgian Ale",
        "Barleywine",
    ]

    for i in range(qty):
        beers.append(
            BeerModel(
                name=f"Beer{i}",
                style=random.choice(styles),
                abv=round(random.triangular(0, 21, 5), 1),
                price=round(random.uniform(0, 250), 1),
            )
        )

    return beers


def test_get_all(client, db_session):
    beers = db_beer_rows_gen(150)
    db_session.add_all(beers)
    db_session.commit()

    response = client.get("/beers/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == min(len(beers), PAGE_LIMIT)

    for i, beer in enumerate(beers):
        assert data[i]["name"] == beer.name
        assert data[i]["style"] == beer.style
        assert data[i]["abv"] == beer.abv
        assert data[i]["price"] == beer.price


def test_get_all_empty_list(client, db_session):
    response = client.get("/beers/")
    assert response.status_code == 200

    data = response.json()
    assert data == []
