from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import os
import json
from langchain_community.chat_models import ChatOpenAI
from models import RoomData, StaffData

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

# === GLOBAL STATE ===
latest_strategy = {"strategy": "", "pricing": []}

# === LOAD DATA ===
forecast = pd.read_json("forecast_output.json")
events = pd.read_csv("events.csv")
sentiment = pd.read_csv("sentiment.csv")

# === LLM WRAPPER ===
def ask_llm(prompt):
    llm = ChatOpenAI(
        temperature=0.3,
        model=openrouter_model,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key="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",
    )
    return llm.predict(prompt)

# === STRATEGY AGENT ===
def strategy_agent(forecast_df, event_df, sentiment_df):
    context = f"""
Forecast:\n{forecast_df.to_string(index=False)}
Events:\n{event_df.to_string(index=False)}
Sentiment:\n{sentiment_df.to_string(index=False)}
"""

    prompt = f"""
You are an AI hotel strategist. Based on the forecast, events, and sentiment data below, return a JSON object describing your strategic recommendations.

Your response **must be valid JSON only**, with the following structure:

{{
  "summary": "<short plain English summary of your overall strategy>",
  "actions": [
    {{
      "type": "update_price",
      "room_type": "<Standard|Deluxe|Suite>",
      "price": <new_price_number>
    }},
    {{
      "type": "flag_day",
      "date": "YYYY-MM-DD",
      "note": "<reason>"
    }},
    {{
      "type": "adjust_staffing",
      "date": "YYYY-MM-DD",
      "staff_count": <number_of_staff>
    }}
  ]
}}

Respond ONLY with the JSON object. Do not include explanations, formatting, or markdown.

### DATA ###
{context}
"""

    raw_output = ask_llm(prompt)

    try:
        parsed = json.loads(raw_output)
        return parsed
    except json.JSONDecodeError:
        print("⚠️ LLM returned non-JSON:", raw_output)
        return {
            "summary": "Error: Could not parse LLM response.",
            "actions": []
        }

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

    result = strategy_agent(forecast_df, event_df, sentiment_df)
    summary = result.get("summary", "No summary.")
    actions = result.get("actions", [])

    # Initial default pricing
    pricing = {
        "Standard": 150,
        "Deluxe": 200,
        "Suite": 300,
    }

    for action in actions:
        if action["type"] == "update_price":
            pricing[action["room_type"]] = action["price"]
        elif action["type"] == "flag_day":
            print(f"📅 Flagged {action['date']}: {action['note']}")
        elif action["type"] == "adjust_staffing":
            print(f"👥 Staffing updated on {action['date']}: {action['staff_count']} staff")

    pricing_list = [{"room_type": k, "price": v} for k, v in pricing.items()]

    latest_strategy = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "summary": summary,
        "strategy": summary,
        "pricing": pricing_list,
        "actions": actions,
        "risk": "⚠️ Negative sentiment trend" if run_sentiment_agent else "✅ Stable"
    }

    print("✅ Strategy Summary:", summary)
    print("✅ Actions:", actions)

# === SCHEDULE MCP ===
scheduler = BackgroundScheduler()
scheduler.add_job(run_mcp)
scheduler.start()

# === API ENDPOINTS ===
@app.get("/recommendation")
def get_recommendation():
    return {
        "summary": latest_strategy.get("summary", ""),
        "pricing": latest_strategy.get("pricing", []),
        "actions": latest_strategy.get("actions", []),
        "risk": latest_strategy.get("risk", "")
    }

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
