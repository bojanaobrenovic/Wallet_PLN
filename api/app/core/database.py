import os
from dotenv import load_dotenv

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from .config import DATABASE_URL

#Connection to the database
engine=create_engine(DATABASE_URL)

#Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency - daje DB sesiju po requestu, uvek je zatvara na kraju."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()