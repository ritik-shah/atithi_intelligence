from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.models import ChatInput
from app.data import latest_strategy, forecast, events, sentiment
from app.llm import ask_llm
from app.mcp import run_mcp
from apscheduler.schedulers.background import BackgroundScheduler

from supabase import create_client
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
SUPABASE_URL = "https://tbycuaukgbqhusmayzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRieWN1YXVrZ2JxaHVzbWF5emNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5MjIyMzYsImV4cCI6MjA2MzQ5ODIzNn0.k-rs3SJ0XaneQjdc1eK-eI5U18cFfdAc3kjNI_yxTJ4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Models for Supabase data

class EventFlag(BaseModel):
    id: int
    date: str
    note: Optional[str]
    source: Optional[str]
    created_at: Optional[str]

class PricingHistory(BaseModel):
    id: int
    date: str
    room_type: str
    base_price: float
    new_price: float
    change_pct: Optional[float]
    note: Optional[str]
    source: Optional[str]
    created_at: Optional[str]

class StaffingLog(BaseModel):
    id: int
    date: str
    staff_on_duty: int
    note: Optional[str]
    source: Optional[str]
    created_at: Optional[str]
    staff_total: Optional[int]
    staff_off_duty: Optional[int]

class StrategyLog(BaseModel):
    id: int
    timestamp: str
    summary: Optional[str]
    pricing_json: Optional[dict]
    actions_json: Optional[dict]
    risk: Optional[str]
    created_at: Optional[str]

def check_error(response):
    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=500, detail=str(response.error))
    if hasattr(response, "status_code") and response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail="Supabase error")
    return response.data


# Your existing endpoints

@app.get("/")
def root():
    return {"message": "Hotel Agentic AI system alive!"}

@app.get("/strategy")
def get_strategy():
    return latest_strategy

@app.get("/data/forecast")
def get_forecast():
    return forecast.to_dict(orient="records")

@app.get("/data/events")
def get_events():
    return events.to_dict(orient="records")

@app.get("/data/sentiment")
def get_sentiment():
    return sentiment.to_dict(orient="records")

@app.post("/chat")
def chat(input: ChatInput):
    answer = ask_llm(input.question)
    return {"answer": answer}

# Supabase data endpoints

from fastapi import Query
from typing import Optional
from datetime import date

@app.get("/supabase/pricing_history", response_model=List[PricingHistory])
def get_pricing_history(
    specific_date: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    query = supabase.table("pricing_history").select("*")

    # Apply range if either start_date or end_date is provided
    if start_date or end_date:
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
    elif specific_date:
        query = query.eq("date", specific_date)

    query = query.order("date", desc=True)
    data = check_error(query.execute())
    return data



@app.get("/supabase/event_flags", response_model=List[EventFlag])
def get_event_flags(
    specific_date: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    query = supabase.table("event_flags").select("*")

    # Priority: If date range is provided, use that
    if start_date or end_date:
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
    elif specific_date:
        query = query.eq("date", specific_date)

    query = query.order("date", desc=True)
    data = check_error(query.execute())
    return data



@app.get("/supabase/staffing_log", response_model=List[StaffingLog])
def get_staffing_log(
    specific_date: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    query = supabase.table("staffing_log").select("*")

    if start_date or end_date:
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
    elif specific_date:
        query = query.eq("date", specific_date)

    query = query.order("date", desc=True)
    data = check_error(query.execute())
    return data


router = APIRouter()

class StrategyLog(BaseModel):
    pricing_json: List[Dict[str, Any]]
    actions_json: List[Dict[str, Any]]
    # Include other fields from the strategy_log table if needed

@router.get("/supabase/strategy_log", response_model=List[StrategyLog])
async def get_strategy_log():
    resp = supabase.table("strategy_log").select("*").order("timestamp", desc=True).execute()
    data = check_error(resp)

    for item in data:
        for field in ["pricing_json", "actions_json"]:
            if field in item and isinstance(item[field], str):
                try:
                    item[field] = json.loads(item[field])
                except json.JSONDecodeError:
                    item[field] = []  # Or handle error as needed

    return data

# Schedule MCP run every 1 hour
scheduler = BackgroundScheduler()
scheduler.add_job(run_mcp, "interval", hours=1)
scheduler.start()
