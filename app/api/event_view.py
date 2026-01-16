from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime
from app.api.models import *
import requests
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete,or_ , and_, func
from sqlalchemy.orm import selectinload 
from app.db.database import get_db
from app.db.models import *
import httpx
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")#dobimo token?
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "DEV_SECRET")
ALGORITHM = "HS256"



urniki = APIRouter()
ICAL_BASE_URL = os.getenv("ICAL_URL")
OPTIMIZER_URL = os.getenv("OPTIMIZER_URL")

#za varnost
def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET ni nastavljen")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Token nima sub")
        return int(sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_same_user(uporabnik_id: int, user_id_from_token: int) -> None:
    if uporabnik_id != user_id_from_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@urniki.get("/health")
def health():
    return {"status": "ok"}

#vrne shranjen urnik uporabnika
@urniki.get('/{uporabnik_id}', response_model = Urnik)
async def index(uporabnik_id:int, db: AsyncSession = Depends(get_db)):#z dependency db odpreš sejo
    q = (
    select(TerminiDB, PredmetiDB, AktivnostiDB)
    .join(UrnikiDB, UrnikiDB.termin_id == TerminiDB.termin_id)
    .outerjoin(PredmetiDB, PredmetiDB.predmet_id == TerminiDB.predmet_id)
    .outerjoin(AktivnostiDB, AktivnostiDB.aktivnost_id == TerminiDB.aktivnost_id)
    .where(UrnikiDB.uporabnik_id == uporabnik_id)
    .order_by(TerminiDB.dan.asc(), TerminiDB.zacetek.asc())
    )

    res = await db.execute(q)
    rows = res.all()

    termini = []
    for (t, p, a) in rows:
        termini.append(
            Termin(
                termin_id=t.termin_id,
                zacetek=t.zacetek,
                dolzina=t.dolzina,
                dan=t.dan,
                lokacija=t.lokacija,
                tip=t.tip,
                predmet=Predmet(predmet_id=p.predmet_id, oznaka=p.oznaka, ime=p.ime) if p else None,
                aktivnost=Aktivnost(aktivnost_id=a.aktivnost_id, oznaka=a.oznaka, ime=a.ime) if a else None,
            )
        )

    return Urnik(uporabnik_id=uporabnik_id, termini=termini)


#dodaj uradni urnik in termine novega uporabnika
@urniki.post('/{uporabnik_id}/dodaj', status_code = 201)
async def dodaj(uporabnik_id: int,user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)): #ko hočeš shranit urnik
    #če hoče resetirat urnik
    require_same_user(uporabnik_id, user_id)
    await db.execute(delete(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id))

    #kliče ical za podatke
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{ICAL_BASE_URL}/podatki/uporabnik/{uporabnik_id}")
    if r.status_code != 200:
        raise HTTPException(502, f"iCal service failed ({r.status_code})")
    
    odg = r.json()   # {"user_id":..., "termini":[...]}]
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

            #kliče ical za termine predmeta
            async with httpx.AsyncClient(timeout=20.0) as client:
                vsi_termini = await client.get(f"{ICAL_BASE_URL}/podatki/termini/{predmet_id}")
            if vsi_termini.status_code != 200:
                raise HTTPException(502, f"iCal service failed ({r.status_code})")

            vsi_termini=odg = vsi_termini.json()

            for f in vsi_termini:
                nov_termin = TerminiDB(
                    predmet_id=predmet_id,
                    zacetek = time.fromisoformat(f["zacetek"]),
                    dolzina=f["dolzina"],
                    lokacija=f["lokacija"],
                    tip=f["tip"],
                    dan = f["dan"]
                )
                db.add(nov_termin)
                await db.flush()
                termini_dodani += 1

        zacetek = time.fromisoformat(t["zacetek"])
        dolzina = t["dolzina"]
        lokacija = t.get("lokacija", "")
        tip = t.get("tip", "")
        termin_id = t["termin_id"]
        dan = t["dan"]
        

        q = select(TerminiDB).where(TerminiDB.predmet_id==p.predmet_id, 
                                                   TerminiDB.zacetek == zacetek,
                                                   TerminiDB.dolzina == dolzina,
                                                   TerminiDB.dan == dan,
                                                   TerminiDB.lokacija ==lokacija,
                                                   TerminiDB.tip == tip
                                                )
        res2 = await db.execute(q)
        termin_db = res2.scalar_one_or_none()
        #če slučajno ni termina uporabnika, ga dodamo
        if termin_db is None:
            nov_termin = TerminiDB(
                predmet_id=predmet_id,
                zacetek=zacetek,
                dolzina=dolzina,
                lokacija=lokacija,
                tip=tip,
                dan = dan
            )
            termin_db = nov_termin
            db.add(nov_termin)
            await db.flush()
            termini_dodani += 1
        q = select(UrnikiDB).where(
            UrnikiDB.termin_id ==termin_db.termin_id,
            UrnikiDB.uporabnik_id == uporabnik_id
            )
        res2 = await db.execute(q)
        nov_urnik = res2.scalar_one_or_none()
        if nov_urnik is None:
            db.add(UrnikiDB(uporabnik_id=uporabnik_id, termin_id=termin_db.termin_id))
            await db.flush()
            povezave += 1
    
    await db.commit()

    return { #izpiše kaj smo spremenili
        "uporabnik_id": uporabnik_id,
        "predmeti_dodani": predmeti_dodani,
        "termini_dodani": termini_dodani,
        "urnik_povezav": povezave,
    }

#dodaj predmet/aktivnost + termin
@urniki.post('/{uporabnik_id}/novTermin', status_code = 201)
async def nov(uporabnik_id: int, termin: Termin,user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    require_same_user(uporabnik_id, user_id)
    predmet = None
    aktivnost = None

    if (termin.predmet is None) == (termin.aktivnost is None):
        raise HTTPException(400, detail="Pošlji ali 'predmet' ali 'aktivnost' (ne oba).")

    
    predmeti_dodani =0
    termini_dodani = 0
    povezave_dodane = 0
    aktivnosti_dodane = 0
    
    termin_id = 0
    if termin.predmet is not None:
        predmet = termin.predmet
        res = await db.execute(select(PredmetiDB).where(PredmetiDB.predmet_id == predmet.predmet_id))
        p = res.scalar_one_or_none()
        if p is None:
            p = PredmetiDB(predmet_id = predmet.predmet_id, oznaka=predmet.oznaka, ime=predmet.ime)
            db.add(p)
            await db.flush()
            predmeti_dodani += 1
        
        res = await db.execute(select(TerminiDB).where(TerminiDB.predmet_id==predmet.predmet_id, 
                                                   TerminiDB.zacetek == termin.zacetek,
                                                   TerminiDB.dolzina == termin.dolzina,
                                                   TerminiDB.dan == termin.dan,
                                                   TerminiDB.lokacija == termin.lokacija,
                                                   TerminiDB.tip == termin.tip
                                                ))
    
        t = res.scalar_one_or_none()
        if t is None:
            t = TerminiDB(predmet_id=predmet.predmet_id, 
                        zacetek =termin.zacetek,
                        dolzina = termin.dolzina,
                        dan = termin.dan,
                        lokacija = termin.lokacija,
                        tip = termin.tip)
        
            db.add(t)
            await db.flush()
            termini_dodani += 1
        
        termin_id = t.termin_id
    else:
        aktivnost = termin.aktivnost

        res = await db.execute(select(AktivnostiDB).where(AktivnostiDB.oznaka == aktivnost.oznaka,
                                                    AktivnostiDB.ime == aktivnost.ime ))
        a = res.scalar_one_or_none()
        if a is None:
            a = AktivnostiDB(oznaka=aktivnost.oznaka, ime=aktivnost.ime)
            db.add(a)
            await db.flush() 
            aktivnosti_dodane += 1

        res = await db.execute(select(TerminiDB).where(TerminiDB.aktivnost_id == a.aktivnost_id,
                                                   TerminiDB.zacetek == termin.zacetek,
                                                   TerminiDB.dolzina == termin.dolzina,
                                                   TerminiDB.dan == termin.dan,
                                                   TerminiDB.lokacija == termin.lokacija,
                                                   TerminiDB.tip == termin.tip
                                                ))
    
        t = res.scalar_one_or_none()
        if t is None:
            t = TerminiDB(aktivnost_id = a.aktivnost_id,
                        zacetek =termin.zacetek,
                        dolzina = termin.dolzina,
                        dan = termin.dan,
                        lokacija = termin.lokacija,
                        tip = termin.tip) 
            db.add(t)
            await db.flush()
            termini_dodani += 1
        termin_id = t.termin_id


    res = await db.execute(
        select(UrnikiDB).where(
            UrnikiDB.uporabnik_id == uporabnik_id,
            UrnikiDB.termin_id == termin_id,
        )
    )
    if res.scalar_one_or_none() is None:
        db.add(UrnikiDB(uporabnik_id=uporabnik_id, termin_id=termin_id))
        povezave_dodane += 1

    await db.commit()
       
    return { #izpiše kaj smo spremenili
        "uporabnik_id": uporabnik_id,
        "predmeti_dodani": predmeti_dodani,
        "aktivnosti_dodane": aktivnosti_dodane,
        "termini_dodani": termini_dodani,
        "povezave_dodane": povezave_dodane,
    }

#shrani nov urnik uporabnika
@urniki.post('/{uporabnik_id}/shrani', status_code = 201)
async def shrani(uporabnik_id: int, urnik:Urnik,user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)): #ko hočeš shranit urnik
    require_same_user(uporabnik_id, user_id)
    await db.execute(delete(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id))
    uporabnik_id = urnik.uporabnik_id

    await db.execute(delete(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id))
    termini = urnik.termini
    povezave = 0
    for t in termini:
        termin_id = t.termin_id
        #ali moram preverit, če predmet/termin obstaja?
        db.add(UrnikiDB(uporabnik_id=uporabnik_id, termin_id=termin_id))
        povezave += 1
    
    await db.commit()

    return { #izpiše kaj smo spremenili
        "uporabnik_id": uporabnik_id,
        "spremenjene_povezave": povezave,
    }

    
@urniki.post('/optimizations/{uporabnik_id}')
async def optimize(uporabnik_id:int, zahteve:Zahteve, db: AsyncSession = Depends(get_db)):
    #klici bazo
    q = (
        select(TerminiDB, PredmetiDB, AktivnostiDB)
        .join(UrnikiDB, UrnikiDB.termin_id == TerminiDB.termin_id)
        .outerjoin(PredmetiDB, PredmetiDB.predmet_id == TerminiDB.predmet_id)
        .outerjoin(AktivnostiDB, AktivnostiDB.aktivnost_id == TerminiDB.aktivnost_id)
        .where(UrnikiDB.uporabnik_id == uporabnik_id)
    )
    res = await db.execute(q)
    rows = res.all()
    
    urnik = [
        Termin(
            termin_id=t.termin_id,
            predmet=(
                Predmet(predmet_id=p.predmet_id, ime=p.ime, oznaka=p.oznaka) if p else None),
            aktivnost=(
                Aktivnost(aktivnost_id=a.aktivnost_id, ime=a.ime, oznaka=a.oznaka)if a else None),
            zacetek=t.zacetek,
            dolzina=t.dolzina,
            dan=t.dan,
            lokacija=t.lokacija,
            tip=t.tip,
        )
        for (t, p, a) in rows
    ]
    predmet_ids = {x.predmet.predmet_id for x in urnik if x.predmet is not None}

    iskanje = []
    if predmet_ids:
        iskanje.append(and_(TerminiDB.predmet_id.in_(predmet_ids), TerminiDB.tip.in_(["LV", "AV"])))


    if not iskanje:
        termini = []
    else:
        q = (
            select(TerminiDB, PredmetiDB, AktivnostiDB)
            .outerjoin(PredmetiDB, PredmetiDB.predmet_id == TerminiDB.predmet_id)
            .outerjoin(AktivnostiDB, AktivnostiDB.aktivnost_id == TerminiDB.aktivnost_id)
            .where(or_(*iskanje))
        )
    
        res = await db.execute(q)
        odg = res.all()

        termini = [
            Termin(
                termin_id=t.termin_id,
                predmet=(
                    Predmet(predmet_id=p.predmet_id, ime=p.ime, oznaka=p.oznaka)
                    if p else None
                ),
                aktivnost=(
                    Aktivnost(aktivnost_id=a.aktivnost_id, ime=a.ime, oznaka=a.oznaka)
                    if a else None
                ),
                zacetek=t.zacetek,
                dolzina=t.dolzina,
                dan=t.dan,
                lokacija=t.lokacija,
                tip=t.tip,
            )
            for (t, p, a) in odg
        ]
    

    u = Urnik(uporabnik_id=uporabnik_id, termini= urnik)
    sporocilo = OptimizeRequest(uporabnik_id = uporabnik_id, urnik=u, zahteve=zahteve, termini=termini)
    async with httpx.AsyncClient(timeout=20.0) as client:
        odg = await client.post(OPTIMIZER_URL,json=jsonable_encoder(sporocilo))
    if odg.status_code != 200:
        raise HTTPException(status_code=odg.status_code, detail=odg.text)

    return odg.json()



@urniki.delete("/{uporabnik_id}/odstrani", status_code=200)
async def odstrani_urnik(uporabnik_id: int,user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
   
    require_same_user(uporabnik_id, user_id)
    await db.execute(delete(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id))    # (opcijsko) preveri, koliko zapisov ima uporabnik
    count_q = select(func.count()).select_from(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id)
    n = (await db.execute(count_q)).scalar_one()

    # pobriši vse povezave uporabnik -> termin
    await db.execute(
        delete(UrnikiDB).where(UrnikiDB.uporabnik_id == uporabnik_id)
    )
    await db.commit()

    return {"ok": True, "deleted_rows": int(n)}
