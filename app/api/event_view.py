
from fastapi import APIRouter, Header
from typing import List
from datetime import time
from app.api.models import Urnik, Termin, Predmet

test_urnik_db = [
    {
        'user_id':63230298,
        'termini':[
            {"termin_id": 1,
            "predmet":{
                "id_predmet": 1,
                "ime": "prpo",
                "oznaka":123,    
                },
            "zacetek":"10:00",
            "konec":"12:00",
            "dan": 0,
            "lokacija":"P16",
            "tip":0
            },
            {"termin_id": 2,
            "predmet":{
                "id_predmet": 2,
                "ime": "oui",
                "oznaka":124,    
                },
            "zacetek":"12:00:00",
            "konec":"14:00:00",
            "dan": 0,
            "lokacija":"P16",
            "tip":0
            }

        ]
    }
]

urniki = APIRouter()

@urniki.get('/', response_model = List[Urnik])
async def index():
    return test_urnik_db #returns JSON

@urniki.post('/', status_code = 201)
async def dodaj_urnik(payload: Urnik):
    urnik = payload.dict()
    #dodaj urnik v bazo
    return {'sporocilo':'urnik ustvarjen'}
#delete dela user ms

#raise HTTPException(status_code=404, detail="napaka") ->dodaj potem