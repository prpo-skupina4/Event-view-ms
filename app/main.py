#run app: uvicorn app.main:app --reload
from fastapi import FastAPI
from app.api.event_view import urniki

app = FastAPI()
app.include_router(urniki)

