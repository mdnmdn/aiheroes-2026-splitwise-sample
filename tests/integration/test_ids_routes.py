"""An id that is out of range or not a number gives the answer of an unknown id."""

import pytest
from fastapi.testclient import TestClient

from app.core.ids import MAX_ID
from app.members import repo as members_repo

HX = {"HX-Request": "true"}
BAD = [str(MAX_ID + 1), "99999999999999999999999", "0", "-3", "abc"]


@pytest.mark.parametrize("bad", BAD)
def test_group_page_bad_id_goes_home_like_an_unknown_id(
    client: TestClient, make_user, auth, bad: str
) -> None:
    headers = {**auth(make_user("Alice")), **HX}
    unknown = client.get("/groups/999", headers=headers)
    response = client.get(f"/groups/{bad}", headers=headers)
    assert response.status_code == unknown.status_code == 200
    assert response.headers["HX-Location"] == unknown.headers["HX-Location"]


@pytest.mark.parametrize("bad", BAD)
def test_group_routes_bad_id_is_404(client: TestClient, make_user, auth, bad: str) -> None:
    headers = {**auth(make_user("Alice")), **HX}
    for url in (
        f"/groups/{bad}/settings",
        f"/groups/{bad}/invite",
        f"/groups/{bad}/members",
        f"/groups/{bad}/members/new",
        f"/groups/{bad}/transactions",
        f"/groups/{bad}/expenses/new",
        f"/groups/{bad}/expenses/preview",
        f"/groups/{bad}/payments/new",
    ):
        assert client.get(url, headers=headers).status_code == 404, url
    for url in (
        f"/groups/{bad}/settings",
        f"/groups/{bad}/members",
        f"/groups/{bad}/expenses",
        f"/groups/{bad}/payments",
    ):
        assert client.post(url, data={"name": "x"}, headers=headers).status_code == 404, url
    leave = client.post(f"/groups/{bad}/leave", headers=headers)
    assert leave.status_code == client.post("/groups/999/leave", headers=headers).status_code


@pytest.mark.parametrize("bad", BAD)
def test_child_ids_bad_id_is_404(
    client: TestClient, make_user, make_group, auth, tmp_db, bad: str
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    headers = {**auth(alice), **HX}
    base = f"/groups/{group.id}"
    for url in (
        f"{base}/members/{bad}",
        f"{base}/expenses/{bad}/edit",
        f"{base}/payments/{bad}/edit",
    ):
        assert client.get(url, headers=headers).status_code == 404, url
    for url in (
        f"{base}/members/{bad}/delete",
        f"{base}/expenses/{bad}",
        f"{base}/expenses/{bad}/delete",
        f"{base}/payments/{bad}",
        f"{base}/payments/{bad}/delete",
    ):
        assert client.post(url, data={"name": "x"}, headers=headers).status_code == 404, url


def test_form_ids_out_of_range_are_validation_errors(
    client: TestClient, make_user, make_group, join_group, auth, tmp_db
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    headers = {**auth(alice), **HX}
    huge = str(MAX_ID + 1)
    expense = {
        "description": "x", "amount": "5", "expense_date": "2026-01-01",
        "payer_id": huge, "p": [huge],
    }  # fmt: skip
    r = client.post(f"/groups/{group.id}/expenses", data=expense, headers=headers)
    assert r.status_code == 422
    payment = {"sender_id": huge, "receiver_id": huge, "amount": "5", "payment_date": "2026-01-01"}
    r = client.post(f"/groups/{group.id}/payments", data=payment, headers=headers)
    assert r.status_code == 422
    r = client.post(f"/groups/{group.id}/members", data={"user_id": huge}, headers=headers)
    assert r.status_code == 422
    r = client.post("/login", data={"user_id": huge}, headers=HX)
    assert r.status_code == 422
    assert len(members_repo.list_members(tmp_db, group.id)) == 2
