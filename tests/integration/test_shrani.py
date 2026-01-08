# tests/integration/test_shrani.py
import pytest

@pytest.mark.anyio
async def test_shrani_rejects_mismatched_user_id(client):
    body = {
        "uporabnik_id": 999,   # != path
        "termini": []
    }
    r = await client.post("/urniki/1/shrani", json=body)
    assert r.status_code == 400
    assert "ne ujemata" in r.json()["detail"]


@pytest.mark.anyio
async def test_shrani_accepts_and_returns_count(client):
    body = {
        "uporabnik_id": 1,
        "termini": [
            {"termin_id": 10, "zacetek": "08:00:00", "dolzina": 60, "dan": 1, "lokacija": "P01", "tip": "P", "predmet": None, "aktivnost": None},
            {"termin_id": 11, "zacetek": "10:00:00", "dolzina": 60, "dan": 1, "lokacija": "P02", "tip": "AV", "predmet": None, "aktivnost": None},
        ],
    }
    r = await client.post("/urniki/1/shrani", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["uporabnik_id"] == 1
    assert data["spremenjene_povezave"] == 2
