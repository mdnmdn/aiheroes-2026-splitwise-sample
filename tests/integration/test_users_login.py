import sqlite3

from fastapi.testclient import TestClient

from app.core.session import COOKIE_NAME, HEADER_NAME, read_token


def _first_user_id(conn: sqlite3.Connection, name: str) -> int:
    return conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()["id"]


def test_login_page_renders_for_no_user(client: TestClient) -> None:
    response = client.get("/login")
    assert response.status_code == 200
    assert 'id="loginForm"' in response.text
    assert '<option value="__new" selected>' in response.text
    assert "Select your name…" not in response.text
    assert "Simulated sign-in: no password needed." in response.text
    assert 'class="skip"' not in response.text
    assert 'id="topbar"' not in response.text


def test_login_page_lists_users_sorted(client: TestClient, sign_in) -> None:
    for name in ("carla", "Alice", "bob"):
        sign_in(name)
    text = client.get("/login").text
    assert "Select your name…" in text
    assert text.index(">Alice<") < text.index(">bob<") < text.index(">carla<")
    assert text.index(">carla<") < text.index("New user…")


def test_new_user_sign_in_sets_cookie(client: TestClient, tmp_db: sqlite3.Connection) -> None:
    response = client.post(
        "/login", data={"user_id": "__new", "name": " Alice ", "next": "/"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    user_id = _first_user_id(tmp_db, "Alice")
    assert read_token(client.cookies.get(COOKIE_NAME)) == user_id
    home = client.get("/")
    assert home.status_code == 200
    assert "Alice" in home.text
    assert "Signed in as Alice." in home.text
    assert "Signed in as" not in client.get("/").text


def test_sign_in_follows_safe_next_only(client: TestClient, sign_in) -> None:
    sign_in("Alice")
    data = {"user_id": "1", "next": "/groups/1?x=1"}
    assert client.post("/login", data=data, follow_redirects=False).headers["location"] == (
        "/groups/1?x=1"
    )
    data["next"] = "//evil.example"
    assert client.post("/login", data=data, follow_redirects=False).headers["location"] == "/"


def test_sign_in_existing_user(client: TestClient, tmp_db: sqlite3.Connection, sign_in) -> None:
    sign_in("Alice")
    response = client.post("/login", data={"user_id": "1"}, follow_redirects=False)
    assert response.status_code == 303
    assert read_token(client.cookies.get(COOKIE_NAME)) == 1
    assert tmp_db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] == 1


def test_sign_in_errors_return_422(client: TestClient, sign_in) -> None:
    sign_in("Alice")
    page = client.post("/login", data={"user_id": ""})
    assert page.status_code == 422
    assert "Choose your name, or pick “New user…”." in page.text
    assert "<html" in page.text
    long_name = client.post("/login", data={"user_id": "__new", "name": "x" * 31})
    assert "Use at most 30 characters." in long_name.text
    empty = client.post("/login", data={"user_id": "__new", "name": "  "})
    assert "Enter a name." in empty.text
    dup = client.post("/login", data={"user_id": "__new", "name": "alice"})
    assert "alice is a user. Pick that user from the list" in dup.text
    assert COOKIE_NAME not in client.cookies


def test_htmx_error_returns_form_fragment(client: TestClient) -> None:
    response = client.post(
        "/login", data={"user_id": "__new", "name": ""}, headers={"HX-Request": "true"}
    )
    assert response.status_code == 422
    assert "<html" not in response.text
    assert 'id="loginForm"' in response.text


def test_htmx_success_redirects_with_session_event(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={"user_id": "__new", "name": "Bob", "next": "/"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/"
    assert "session-start" in response.headers["HX-Trigger"]
    assert COOKIE_NAME in client.cookies


def test_header_token_beats_cookie(client: TestClient, sign_in) -> None:
    alice = sign_in("Alice")
    bob = sign_in("Bob")
    client.post("/login", data={"user_id": "1"})
    assert 'data-user-id="1"' in client.get("/").text
    page = client.get("/", headers=bob)
    assert 'data-user-id="2"' in page.text
    assert "Account: Bob" in page.text
    assert 'data-user-id="1"' in client.get("/", headers=alice).text


def test_bad_token_counts_as_no_user(client: TestClient) -> None:
    response = client.get("/", headers={HEADER_NAME: "garbage"}, follow_redirects=False)
    assert response.status_code == 303


def test_signed_out_home_redirects_to_login(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/"


def test_htmx_signed_out_gets_hx_redirect(client: TestClient) -> None:
    response = client.get("/", headers={"HX-Request": "true"}, follow_redirects=False)
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/login?next=/"


def test_logout_clears_cookie(client: TestClient) -> None:
    client.post("/login", data={"user_id": "__new", "name": "Alice"})
    assert client.get("/").status_code == 200
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert COOKIE_NAME not in client.cookies
    assert client.get("/", follow_redirects=False).status_code == 303


def test_signed_in_user_can_open_login(client: TestClient, sign_in) -> None:
    client.post("/login", data={"user_id": "__new", "name": "Alice"})
    assert client.get("/login").status_code == 200


def test_topbar_shows_user_and_group_count(client: TestClient, tmp_db: sqlite3.Connection) -> None:
    client.post("/login", data={"user_id": "__new", "name": "Alice"})
    text = client.get("/").text
    assert "Account: Alice" in text
    assert "Signed in · 0 groups" in text
    assert 'action="/logout"' in text


def test_huge_user_id_is_a_form_error_not_a_crash(client: TestClient) -> None:
    response = client.post("/login", data={"user_id": "9" * 20})
    assert response.status_code == 422
    assert "Choose your name, or pick “New user…”." in response.text


def test_resume_sets_cookie_from_header(client: TestClient, sign_in) -> None:
    headers = sign_in("Alice")
    response = client.post("/login/resume", headers=headers)
    assert response.status_code == 204
    assert COOKIE_NAME in response.headers["set-cookie"]
    assert client.cookies.get(COOKIE_NAME) == headers[HEADER_NAME]


def test_resume_rejects_missing_bad_and_unknown_token(client: TestClient) -> None:
    from app.core.session import sign_token

    for headers in ({}, {HEADER_NAME: "garbage"}, {HEADER_NAME: sign_token(999)}):
        response = client.post("/login/resume", headers=headers)
        assert response.status_code == 401
        assert "Max-Age=0" in response.headers["set-cookie"]


def test_resume_ignores_the_cookie(client: TestClient, sign_in) -> None:
    client.cookies.set(COOKIE_NAME, sign_in("Alice")[HEADER_NAME])
    response = client.post("/login/resume")
    assert response.status_code == 401
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_login_page_with_cookie_user_shows_the_form(client: TestClient) -> None:
    client.post("/login", data={"user_id": "__new", "name": "Alice"})
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 200
    assert 'id="loginForm"' in response.text


def test_base_renders_guard_attributes_and_script(client: TestClient, sign_in) -> None:
    login = client.get("/login").text
    assert '<html lang="en" data-user-id="" data-public>' in login
    assert "/login/resume" in login
    assert "html.sw-resuming{visibility:hidden}" in login
    assert login.index("/login/resume") < login.index("splitwise.css")
    home = client.get("/", headers=sign_in("Alice")).text
    assert '<html lang="en" data-user-id="1">' in home
    assert "data-public>" not in home
