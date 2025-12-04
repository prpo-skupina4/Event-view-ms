from typing import List
from pydantic import BaseModel
from datetime import time


class Predmet(BaseModel):
    id_predmet: int
    ime: str
    oznaka: int 

class Termin(BaseModel):
    termin_id: int
    predmet: Predmet
    zacetek: time
    konec: time
    dan: int
    lokacija: str
    tip:int


class Urnik(BaseModel):
    user_id: int
    termini: List[Termin]