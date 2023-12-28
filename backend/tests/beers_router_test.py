import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.main import app
from backend import models
from backend.schemas import Beer, BeerCreate

client = TestClient(app)


@pytest.fixture
def mock_db_session():
    session = Mock(spec=Session)
    return session


def test_get_beers(mock_db_session):
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.get("/beers/")
        assert response.status_code == 200


def test_get_beer_by_id_found(mock_db_session):
    mock_beer = models.Beer(beer_id=1, name="Test Beer", style="IPA", abv=5.0)
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_beer
    )
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.get("/beers/1")
        assert response.status_code == 200
        assert response.json() == {
            "beer_id": 1,
            "name": "Test Beer",
            "style": "IPA",
            "abv": 5.0,
        }


def test_get_beer_by_id_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.get("/beers/999")
        assert response.status_code == 404


def test_create_beer(mock_db_session):
    beer_data = {"name": "Test Beer", "style": "IPA", "abv": 5.0}
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.post("/beers/", json=beer_data)
        assert response.status_code == 201
        assert response.json() == beer_data


def test_delete_beer_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        models.Beer()
    )
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.delete("/beers/1")
        assert response.status_code == 204


def test_delete_beer_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.delete("/beers/999")
        assert response.status_code == 404


def test_update_beer_found(mock_db_session):
    beer_data = {"name": "Updated Beer", "style": "IPA", "abv": 6.0}
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        models.Beer()
    )
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.put("/beers/1", json=beer_data)
        assert response.status_code == 200
        assert response.json() == beer_data


def test_update_beer_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    with patch("backend.database.get_db", return_value=mock_db_session):
        response = client.put("/beers/999", json={"name": "Updated Beer"})
        assert response.status_code == 404
