from sqlalchemy import Column, Integer, String, Float, DateTime
from src.database import Base


class Audio(Base):
    __tablename__ = "audio"

    id                      = Column(Integer, primary_key=True)
    create_date             = Column(DateTime, nullable=False)
    original_audio_path     = Column(String)
    original_text           = Column(String, nullable=False)
    processed_audio_path    = Column(String, nullable=False)
    processed_text          = Column(String)
    onset                   = Column(Float)
    offset                  = Column(Float)


class User(Base):
    __tablename__ = "user"

    id       = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email    = Column(String, unique=True, nullable=False)