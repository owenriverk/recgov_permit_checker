from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

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
