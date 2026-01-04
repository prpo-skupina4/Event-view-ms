from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from app.api.models import Urnik, Termin, Predmet, Zahteve
import requests
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.db.models import UrnikiDB, TerminiDB, PredmetiDB
import httpx



urniki = APIRouter()
ICAL_BASE_URL = os.getenv("ICAL_BASE_URL", "http://127.0.0.1:8001")

@urniki.get('/{uporabnik_id}', response_model = Urnik)
async def index(uporabnik_id:int, db: AsyncSession = Depends(get_db)):#z dependency db odpreš sejo
    q = (
        select(TerminiDB, PredmetiDB)
        .join(UrnikiDB, UrnikiDB.termin_id == TerminiDB.termin_id)
        .join(PredmetiDB, PredmetiDB.predmet_id==TerminiDB.predmet_id)
        .where(UrnikiDB.uporabnik_id == uporabnik_id)#izberi urnik uporabnika
        .order_by(TerminiDB.zacetek.asc())
    )
    res = await db.execute(q) #čakaš poizvedbo
    rows = res.all() #odgovor poizvedbe

    #klici vreme?
    termini = [
        Termin(
            termin_id=t.termin_id,
            zacetek=t.zacetek,
            konec=t.konec,
            lokacija=t.lokacija,
            tip=t.tip,
            dan=t.zacetek.weekday(),
            predmet=Predmet(
                predmet_id=p.predmet_id,
                oznaka=p.oznaka,
                ime=p.ime
            ),
        )
        for (t, p) in rows
    ]
    return Urnik(uporabnik_id=uporabnik_id, termini=termini)

@urniki.post('/{uporabnik_id}/dodaj', status_code = 201)
async def dodaj(uporabnik_id: int, db: AsyncSession = Depends(get_db)): #ko hočeš shranit urnik
    await db.execute(delete(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id))

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{ICAL_BASE_URL}/podatki/uporabnik/{uporabnik_id}")
    if r.status_code != 200:
        raise HTTPException(502, f"iCal service failed ({r.status_code})")
    
    odg = r.json()   # {"user_id":..., "termini":[...]}]
    uporabnik_id = odg["uporabnik_id"]
    termini = odg["termini"]
    predmeti_dodani = 0
    termini_dodani = 0
    povezave = 0
    
    for t in termini:
        predmet = t["predmet"]
        predmet_id = predmet["predmet_id"]
        #dodamo predmet, če ga ni v bazi
        res = await db.execute(select(PredmetiDB).where(PredmetiDB.predmet_id == predmet_id))
        
        p = res.scalar_one_or_none()
        if p is None:#dodamo predmet in njegove termine, če ga še ni
            ime = predmet["ime"]
            oznaka = predmet["oznaka"]
            p = PredmetiDB(predmet_id = predmet_id, oznaka=oznaka, ime=ime)
            db.add(p)
            await db.flush()
            predmeti_dodani += 1

            async with httpx.AsyncClient(timeout=20.0) as client:
                vsi_termini = await client.get(f"{ICAL_BASE_URL}/podatki/termini/{predmet_id}")
            if vsi_termini.status_code != 200:
                raise HTTPException(502, f"iCal service failed ({r.status_code})")

            vsi_termini=odg = vsi_termini.json()

            for f in vsi_termini:
                termin_db = TerminiDB(
                    termin_id = f["termin_id"],
                    predmet_id=predmet_id,
                    zacetek=datetime.fromisoformat(f["zacetek"]),
                    konec=datetime.fromisoformat(f["konec"]),
                    lokacija=f["lokacija"],
                    tip=f["tip"],
                )
                db.add(termin_db)
                await db.flush()
                termini_dodani += 1

        zacetek = datetime.fromisoformat(t["zacetek"])
        konec = datetime.fromisoformat(t["konec"])
        lokacija = t.get("lokacija", "")
        tip = t.get("tip", "")
        termin_id = t["termin_id"]

        q = select(TerminiDB).where(
            TerminiDB.termin_id ==termin_id,
            TerminiDB.predmet_id == predmet_id,
            TerminiDB.zacetek == zacetek,
            TerminiDB.konec == konec,
            TerminiDB.tip == tip,
            TerminiDB.lokacija == lokacija,
        )
        res2 = await db.execute(q)
        termin_db = res2.scalar_one_or_none()
        #če slučajno ni termina uporabnika, ga dodamo
        if termin_db is None:
            termin_db = TerminiDB(
                termin_id = termin_id,
                predmet_id=predmet_id,
                zacetek=zacetek,
                konec=konec,
                lokacija=lokacija,
                tip=tip,
            )
            db.add(termin_db)
            await db.flush()
            termini_dodani += 1
        db.add(UrnikiDB(uporabnik_id=uporabnik_id, termin_id=termin_id))
        
        povezave += 1
    
    await db.commit()

    return { #izpiše kaj smo spremenili
        "uporabnik_id": uporabnik_id,
        "predmeti_dodani": predmeti_dodani,
        "termini_dodani": termini_dodani,
        "urnik_povezav": povezave,
    }

@urniki.post('/optimizations/{uporabnik_id}')
def optimize(uporabnik_id, zahteve):
    #klici bazo
    urnik = []
    sporocilo ={
        "uporbnik_id": uporabnik_id,
        "urnik": urnik,
        "zahteve": zahteve
    }
    odg = requests.post(optimizer_URL, json=sporocilo)
    if odg.status_code != 200:
        raise HTTPException(status_code=500, detail="optimizator failed")
    return odg.json()