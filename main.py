from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time
import pandas as pd
import os
from langchain_community.chat_models import ChatOpenAI

# === CONFIG ===
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["OPENAI_API_KEY"] = "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"
openrouter_model = "mistralai/mixtral-8x7b-instruct"

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === GLOBAL VARIABLES (Mock DB for now) ===
latest_strategy = {"strategy": "", "pricing": []}

# === LOAD DATA (You can reload inside MCP if needed) ===
forecast = pd.read_json("forecast_output.json")
events = pd.read_csv("events.csv")
sentiment = pd.read_csv("sentiment.csv")

# === AGENT LOGIC (reused from your script) ===
def ask_llm(prompt):
    llm = ChatOpenAI(
        temperature=0.3,
        model=openrouter_model,
        openai_api_base=os.environ["OPENAI_API_BASE"],
        openai_api_key=os.environ["OPENAI_API_KEY"]
    )
    return llm.predict(prompt)

def strategy_agent(forecast_df, event_df, sentiment_df):
    context = f"""
Forecast:\n{forecast_df.to_string(index=False)}
Events:\n{event_df.to_string(index=False)}
Sentiment:\n{sentiment_df.to_string(index=False)}
"""
    prompt = f"""
You are an AI hotel strategist. Based on the forecast, events, and sentiment, write an action plan:
- Identify high/low demand days
- Suggest pricing/staffing strategy
- Call out any risks/opportunities

Data:\n{context}
"""
    return ask_llm(prompt)

# === MCP LOGIC ===
def run_mcp():
    print("🚦 MCP running...")
    global latest_strategy

    forecast_df = forecast
    high_demand_days = forecast_df[forecast_df["yhat"] > forecast_df["yhat"].mean() + 10]
    low_demand_days = forecast_df[forecast_df["yhat"] < forecast_df["yhat"].mean() - 10]

    run_event_agent = len(high_demand_days) >= 3
    run_sentiment_agent = sentiment["sentiment_score"].mean() < 0

    event_df = events if run_event_agent else pd.DataFrame(columns=events.columns)
    sentiment_df = sentiment if run_sentiment_agent else pd.DataFrame(columns=sentiment.columns)

    rec = strategy_agent(forecast_df, event_df, sentiment_df)
    
    # Mock price extraction (you can make this smarter)
    pricing = [
        {"room_type": "Standard", "price": 150},
        {"room_type": "Deluxe", "price": 200},
        {"room_type": "Suite", "price": 300},
    ]

    latest_strategy = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "strategy": rec,
        "pricing": pricing,
        "risk": "⚠️ Negative sentiment trend" if run_sentiment_agent else "✅ Stable"
    }

# Schedule MCP run every 30s
scheduler = BackgroundScheduler()
scheduler.add_job(run_mcp, "interval", seconds=30)
scheduler.start()

# === API ENDPOINTS ===
@app.get("/recommendation")
def get_recommendation():
    return latest_strategy

@app.get("/pricing")
def get_pricing():
    return latest_strategy.get("pricing", [])

class ChatInput(BaseModel):
    question: str

@app.post("/chat")
def ask_question(input: ChatInput):
    context = f"""
Previous Strategy:\n{latest_strategy.get("strategy", "N/A")}
Forecast:\n{forecast.to_string(index=False)}
Events:\n{events.to_string(index=False)}
Sentiment:\n{sentiment.to_string(index=False)}
"""
    prompt = f"""You are an AI hotel strategist.

User asks: "{input.question}"

Based on the previous recommendation and the context below, provide a helpful response.

{context}
"""
    response = ask_llm(prompt)
    return {"response": response}

@app.get("/")
def root():
    return {"message": "Agentic AI Hotel Backend is running 🚀"}
