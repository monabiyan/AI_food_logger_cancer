import os
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Database imports
from database import SessionLocal, engine
import models

# Initialize Database
models.Base.metadata.create_all(bind=engine)


# GPT-4 Configuration
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_BASE"] = "https://pmedgpt4.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "9580dd8c74ca4270ae06022f7caacb1a"
os.environ["OPENAI_API_VERSION"] = "2023-05-15"

from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# FastAPI App
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# GPT-4 Configuration
llm = AzureChatOpenAI(temperature=0.0, deployment_name='gpt-4')
prompt = PromptTemplate(
    input_variables=["raw_text", "current_datetime"],
    template="""
You are a system that extracts meal information from text. 
The user will describe what they ate in natural language. 
You must output a JSON array of objects with fields:
[
  {{ 
    "food": (string), 
    "amount": (string or number if indicated), 
    "hour": (string if mentioned, else "unspecified"),
    "date": (string, default to today's date if not mentioned)
  }}
]
If any info is missing, mark it as "unspecified".

Current DateTime: {current_datetime}
Raw text: {raw_text}
""".strip(),
)
chain = LLMChain(llm=llm, prompt=prompt)


# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class MealLog(BaseModel):
    id: int
    patient_id: str
    food: str
    amount: str
    hour: str
    date: str
    recorded_at: datetime
    raw_text: str


class TextInput(BaseModel):
    patient_id: str
    text: str


# Routes
@app.get("/", response_class=HTMLResponse)
def serve_home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.post("/process-text")
async def process_text(data: TextInput, db: Session = Depends(get_db)):
    try:
        current_datetime = datetime.utcnow().isoformat()
        gpt_response = chain.run(raw_text=data.text, current_datetime=current_datetime)
        structured_data = json.loads(gpt_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {e}")

    for entry in structured_data:
        meal_record = models.MealRecord(
            patient_id=data.patient_id,
            food=entry.get('food', 'unspecified'),
            amount=entry.get('amount', 'unspecified'),
            hour=entry.get('hour', 'unspecified'),
            date=entry.get('date', datetime.utcnow().strftime("%Y-%m-%d")),
            recorded_at=datetime.utcnow(),
            raw_text=data.text
        )
        db.add(meal_record)

    db.commit()
    return {"message": "Text processed and saved successfully", "structured_data": structured_data}


@app.get("/meal-logs/")
def get_all_logs(db: Session = Depends(get_db)):
    logs = db.query(models.MealRecord).all()
    return [
        {
            "id": log.id,
            "patient_id": log.patient_id,
            "food": log.food,
            "amount": log.amount,
            "hour": log.hour,
            "date": log.date,
            "recorded_at": log.recorded_at.isoformat(),
            "raw_text": log.raw_text
        }
        for log in logs
    ]


@app.delete("/delete-log/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(models.MealRecord).filter(models.MealRecord.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    db.delete(log)
    db.commit()
    return {"message": "Log entry deleted successfully"}


@app.put("/update-log/{log_id}")
def update_log(log_id: int, updated_data: dict, db: Session = Depends(get_db)):
    log = db.query(models.MealRecord).filter(models.MealRecord.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")

    # Update fields explicitly
    log.food = updated_data.get('food', log.food)
    log.amount = updated_data.get('amount', log.amount)
    log.hour = updated_data.get('hour', log.hour)
    log.date = updated_data.get('date', log.date)

    db.commit()
    db.refresh(log)  # Ensure the latest state is returned

    return {"message": "Log entry updated successfully", "updated_log": {
        "id": log.id,
        "patient_id": log.patient_id,
        "food": log.food,
        "amount": log.amount,
        "hour": log.hour,
        "date": log.date,
        "recorded_at": log.recorded_at.isoformat()
    }}

