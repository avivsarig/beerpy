import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db

from backend.models import Beer as BeerModel
from backend.schemas import Beer, BeerCreate

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



def test_get_all_beers(client, db_session):
    beers = [
        BeerModel(name="Beer1", style="Ale", abv=5.0, price=10.0),
        BeerModel(name="Beer2", style="Lager", abv=4.5, price=8.0),
    ]
    db_session.add_all(beers)
    db_session.commit()

    response = client.get("/beers/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(beers)

    for i, beer in enumerate(beers):
        assert data[i]["name"] == beer.name
        assert data[i]["style"] == beer.style
        assert data[i]["abv"] == beer.abv
        assert data[i]["price"] == beer.price
