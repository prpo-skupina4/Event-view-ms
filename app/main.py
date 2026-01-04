#run app: uvicorn app.main:app --reload
from fastapi import FastAPI
from app.db import models
from app.db.database import engine, Base
from app.api.event_view import urniki


app = FastAPI()
app.include_router(urniki, prefix="/urniki")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

