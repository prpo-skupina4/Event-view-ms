#run app: uvicorn app.main:app --reload
from fastapi import FastAPI
from app.db import models
from app.db.database import engine, Base
from app.api.event_view import urniki
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(urniki, prefix="/urniki")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
