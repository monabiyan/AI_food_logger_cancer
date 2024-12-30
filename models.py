from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite database URL
DATABASE_URL = "sqlite:///./meals.db"

# Database Engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Model
Base = declarative_base()

# MealRecord Model
class MealRecord(Base):
    __tablename__ = "meal_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    food = Column(String)
    amount = Column(String)
    hour = Column(String)
    date = Column(String, default=datetime.utcnow().date().isoformat())
    recorded_at = Column(DateTime, default=datetime.utcnow)
    raw_text = Column(String)
