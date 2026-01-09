# tests/integration/test_get_urnik.py
import pytest
from datetime import time
from sqlalchemy import delete

from app.db.models import PredmetiDB, TerminiDB, UrnikiDB

@pytest.mark.anyio
async def test_get_urnik_sorted_by_day_and_time(client, db_session):

    await db_session.execute(
        delete(PredmetiDB).where(PredmetiDB.predmet_id == 1)
    )
    await db_session.execute(
        delete(TerminiDB).where(TerminiDB.predmet_id == 1)
    )
    await db_session.execute(
        delete(UrnikiDB).where(UrnikiDB.uporabnik_id == 42)
    )
    await db_session.commit()
    # seed DB: 1 predmet, 2 termina (out of order), 2 povezavi v UrnikiDB
    p = PredmetiDB(predmet_id=1, oznaka="PRPO", ime="PRPO")
    db_session.add(p)
    await db_session.flush()

    t2 = TerminiDB(predmet_id=1, zacetek=time(10, 0), dolzina=90, dan=1, lokacija="P02", tip="AV")
    t1 = TerminiDB(predmet_id=1, zacetek=time(8, 0), dolzina=90, dan=1, lokacija="P01", tip="P")
    db_session.add_all([t2, t1])
    await db_session.flush()

    db_session.add_all([
        UrnikiDB(uporabnik_id=42, termin_id=t2.termin_id),
        UrnikiDB(uporabnik_id=42, termin_id=t1.termin_id),
    ])
    await db_session.commit()

    r = await client.get("/urniki/42")
    assert r.status_code == 200
    data = r.json()
    assert data["uporabnik_id"] == 42
    assert len(data["termini"]) == 2

    # mora biti sorted: dan asc, zacetek asc
    assert data["termini"][0]["zacetek"] == "08:00:00"
    assert data["termini"][1]["zacetek"] == "10:00:00"
