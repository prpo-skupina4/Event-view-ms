# tests/integration/test_dodaj_ical.py
import pytest
import respx
from httpx import Response


from app.db.models import PredmetiDB

ICAL_BASE_URL = os.getenv("ICAL_URL")
@pytest.mark.anyio
@respx.mock
async def test_dodaj_calls_ical_and_creates_subjects(client, db_session):
    await db_session.commit()
    # iCal mock: uporabnik dobi 1 termin iz predmeta 1
    respx.get(f"{ICAL_BASE_URL}/podatki/uporabniki/7").mock(
        return_value=Response(
            200,
            json={
                "uporabnik_id": 7,
                "termini": [
                    {
                        "termin_id": 123,
                        "predmet": {"predmet_id": 1, "oznaka": "PRPO", "ime": "PRPO"},
                        "zacetek": "08:00:00",
                        "dolzina": 90,
                        "dan": 1,
                        "lokacija": "P01",
                        "tip": "P",
                    }
                ],
            },
        )
    )

    # iCal mock: vsi termini predmeta 1 (da endpoint napolni TerminiDB)
    respx.get(f"{ICAL_BASE_URL}/podatki/termini/1").mock(
        return_value=Response(
            200,
            json=[
                {
                    "zacetek": "08:00:00",
                    "dolzina": 90,
                    "dan": 1,
                    "lokacija": "P01",
                    "tip": "P",
                }
            ],
        )
    )

    r = await client.post("/urniki/7")
    assert r.status_code == 201
    data = r.json()
    assert data["uporabnik_id"] == 7
    assert data["predmeti_dodani"] >= 1

    # DB assert: predmet obstaja
    p = await db_session.get(PredmetiDB, 1)
    assert p is not None
