from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class Predmet(BaseModel):
    predmet_id: int
    oznaka: str
    ime: str

class Termin(BaseModel):
    termin_id: int
    predmet: Predmet
    zacetek: datetime
    konec: datetime
    dan:int
    lokacija: str
    tip:str


class Urnik(BaseModel):
    uporabnik_id: int #ali rabim userja ali samo njegov id?
    termini: List[Termin]

class Zahteve(BaseModel):
    zacetek: Optional[datetime] = None
    konec: Optional[datetime] = None
    prosti_dnevi: Optional[List[str]] = None