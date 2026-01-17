# Event-view-ms

Mikrostoritev event-view skrbi za shranjevanje in upravljanje uporabniških urnikov (terminov) ter klic optimizatorja za predlog optimiziranega urnika.

Ogrodja:
- FastAPI
- SQLAlchemy
- JWT
- zunanje mikrostoritve: iCal-ms (uvoz podatkov), optimizer-ms (optimizacije)

Naloge mikrostoritve:
- Prebere shranjen urnik uporabnika iz baze.
- Uvozi “uradni” urnik iz iCal mikrostoritve in ga shrani v bazo (predmeti, termini, povezave).
- Doda posamezen termin (predmet ali aktivnost).
- Shrani urnik z novim seznamom terminov.
- Pošlje podatke optmizatorju in vrne rezultat.
- Pobriše urnik uporabnika (povezave) in po potrebi odstrani termine.

Okoljske spremenljivke:
- JWT_SECRET
- ICAL_URL
- OPTIMIZER_URL

Pisanje in brisanje baze zahteva avtentikacijo.

API Endpoints so opisani v /docs.
