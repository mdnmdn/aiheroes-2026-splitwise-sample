from fastapi.testclient import TestClient

from app.core.session import HEADER_NAME


def test_create_user_returns_token_that_signs_in(client: TestClient) -> None:
    response = client.post("/api/v1/users", json={"name": "Eve"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Eve" and data["token"]
    me = client.get("/api/v1/me", headers={HEADER_NAME: data["token"]})
    assert me.status_code == 200
    assert me.json() == {"id": data["id"], "name": "Eve"}


def test_create_user_invalid_name_is_422_with_fields(client: TestClient) -> None:
    response = client.post("/api/v1/users", json={"name": "  "})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_failed" and "name" in error["fields"]


def test_create_user_duplicate_name_is_422(client: TestClient) -> None:
    client.post("/api/v1/users", json={"name": "Eve"})
    response = client.post("/api/v1/users", json={"name": "Eve"})
    assert response.status_code == 422 and "name" in response.json()["error"]["fields"]


def test_list_users_and_me(client: TestClient, sign_in) -> None:
    alice = sign_in("Alice")
    sign_in("Bob")
    names = [u["name"] for u in client.get("/api/v1/users", headers=alice).json()]
    assert names == ["Alice", "Bob"]
    assert client.get("/api/v1/me", headers=alice).json()["name"] == "Alice"


def test_users_and_me_need_auth(client: TestClient) -> None:
    for path in ("/api/v1/users", "/api/v1/me"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["error"] == {
            "code": "not_signed_in",
            "message": "Sign in first",
            "fields": {},
        }


def test_bad_token_is_401(client: TestClient) -> None:
    assert client.get("/api/v1/me", headers={HEADER_NAME: "junk"}).status_code == 401


def test_cookie_also_signs_in(client: TestClient) -> None:
    token = client.post("/api/v1/users", json={"name": "Eve"}).json()["token"]
    client.cookies.set("sw_user", token)
    assert client.get("/api/v1/me").status_code == 200
