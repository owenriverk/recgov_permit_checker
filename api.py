from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from Models import Preference as DBPreference, SessionLocal, init_db
from sqlalchemy.orm import Session
from datetime import datetime


app = FastAPI()

# Dummy preference storage
preferences = []

class Preference(BaseModel):
    email: str
    sections: List[str]
    start_date: str
    end_date: str

@app.get("/")
def root():
    return {"message": "Permit checker is running!"}

@app.post("/preferences")
def save_preferences(pref: Preference):
    preferences.append(pref)
    return {"status": "saved", "total_preferences": len(preferences)}

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/preferences")
def save_preferences(pref: Preference):
    db: Session = SessionLocal()
    try:
        for section in pref.sections:
            record = DBPreference(
                email=pref.email,
                section=section,
                start_date=datetime.fromisoformat(pref.start_date),
                end_date=datetime.fromisoformat(pref.end_date)
            )
            db.add(record)
        db.commit()
        return {"status": "saved"}
    finally:
        db.close()
