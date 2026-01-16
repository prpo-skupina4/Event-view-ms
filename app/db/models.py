from sqlalchemy import Integer, String, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import time
from .database import Base

class PredmetiDB(Base):
    __tablename__="predmeti"
    
    predmet_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    oznaka: Mapped[str] = mapped_column(String(50))
    ime: Mapped[str] = mapped_column(String(200))

class TerminiDB(Base):
    __tablename__="termini"

    termin_id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    predmet_id = mapped_column(ForeignKey("predmeti.predmet_id"), nullable=True)
    aktivnost_id = mapped_column(ForeignKey("aktivnosti.aktivnost_id"), nullable=True)#za zunanje aktivnosti
    zacetek: Mapped[time] = mapped_column(Time, index=True)
    dolzina: Mapped[int] = mapped_column(Integer, index=True)
    dan:Mapped[int] = mapped_column(Integer, index=True)
    lokacija: Mapped[str] = mapped_column(String(50), nullable=True)
    tip: Mapped[str] = mapped_column(String(50), nullable=True) #vaje, predavanje, drugo

class AktivnostiDB(Base):
    __tablename__ = "aktivnosti"

    aktivnost_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    oznaka: Mapped[str] = mapped_column(String(50))
    ime: Mapped[str] = mapped_column(String(200))

class UrnikiDB(Base):
    __tablename__="urniki"

    uporabnik_id:Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    termin_id:Mapped[int] = mapped_column(ForeignKey("termini.termin_id"), primary_key=True, index=True)