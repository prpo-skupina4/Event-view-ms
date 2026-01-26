# tests/integration/test_shrani.py
import pytest


@pytest.mark.anyio
async def test_shrani_forbidden_when_path_user_is_not_token_user(client):
    r = await client.put("/urniki/1", json={"uporabnik_id": 1, "termini": []})
    assert r.status_code == 403

@pytest.mark.anyio
async def test_shrani_returns_body_user_id_when_authorized(client):
    body = {"uporabnik_id": 999, "termini": []}
    r = await client.put("/urniki/7", json=body)
    assert r.status_code == 201
    assert r.json()["uporabnik_id"] == 999

@pytest.mark.anyio
async def test_shrani_accepts_and_returns_count(client):
    body = {
        "uporabnik_id": 7,
        "termini": [
            {"termin_id": 10, "zacetek": "08:00:00", "dolzina": 60, "dan": 1, "lokacija": "P01", "tip": "P", "predmet": None, "aktivnost": None},
            {"termin_id": 11, "zacetek": "10:00:00", "dolzina": 60, "dan": 1, "lokacija": "P02", "tip": "AV", "predmet": None, "aktivnost": None},
        ],
    }
    r = await client.put("/urniki/7", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["uporabnik_id"] == 7
    assert data["spremenjene_povezave"] == 2


