import pytest
from app import app  # create_app
from requests.auth import _basic_auth_str


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_hello(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json == {'message': 'HELLO'}


def test_users(client):
    response = client.get("/api/users", headers={"Authorization": _basic_auth_str("yuri", "123")})
    assert response.status_code == 200
    assert response.json == {
        "users": [
            {
                "id": 1,
                "username": "yuri"
            },
            {
                "id": 2,
                "username": "oxana"
            },
            {
                "id": 3,
                "username": "maxim"
            }
        ]
    }
