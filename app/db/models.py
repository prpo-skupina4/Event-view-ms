from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .database import Base

class PredmetiDB(Base):
    __tablename__="predmeti"
    
    predmet_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    oznaka: Mapped[str] = mapped_column(String(50))
    ime: Mapped[str] = mapped_column(String(200))

class TerminiDB(Base):
    __tablename__="termini"

    termin_id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    predmet_id: Mapped[int] = mapped_column(ForeignKey("predmeti.predmet_id"), index=True)
    zacetek: Mapped[datetime] = mapped_column(DateTime, index=True) #dan dobiš tukaj: termin.zacetek.weekday()
    konec: Mapped[datetime] = mapped_column(DateTime, index=True)
    lokacija: Mapped[str] = mapped_column(String(50))
    tip: Mapped[str] = mapped_column(String(50)) #vaje, predavanje, drugo

class UrnikiDB(Base):
    __tablename__="urniki"

    uporabnik_id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    termin_id:Mapped[int] = mapped_column(ForeignKey("termini.termin_id"), primary_key=True, index=True)