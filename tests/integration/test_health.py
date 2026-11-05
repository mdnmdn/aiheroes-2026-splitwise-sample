from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_id_is_returned_and_reused(client: TestClient) -> None:
    assert len(client.get("/healthz").headers["X-Request-ID"]) == 32
    assert client.get("/healthz", headers={"X-Request-ID": "abc"}).headers["X-Request-ID"] == "abc"


def test_home_page_renders(client: TestClient, sign_in) -> None:
    response = client.get("/", headers=sign_in("Alice"))
    assert response.status_code == 200
    assert "Your groups" in response.text
    assert 'hx-boost="true"' in response.text


def test_static_files(client: TestClient) -> None:
    assert client.get("/static/vendor/htmx.min.js").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200


def test_unknown_path_html_and_api(client: TestClient) -> None:
    assert client.get("/nope").status_code == 404
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    htmx_response = client.get("/nope", headers={"HX-Request": "true"})
    assert htmx_response.status_code == 404
    assert "<html" not in htmx_response.text


def test_startup_applies_migrations(client: TestClient, tmp_db) -> None:
    rows = tmp_db.execute("SELECT version FROM schema_migrations").fetchall()
    assert [r["version"] for r in rows] == [1]
    assert get_settings().database_path.exists()
