from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agentic AI Hotel Backend")

# Enable CORS for local frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Data Models ===

class PriceUpdate(BaseModel):
    date: str  # e.g. "2025-01-15"
    room_type: str  # e.g. "Deluxe"
    new_price: float
    reason: Optional[str] = None

class StrategyNews(BaseModel):
    id: int
    title: str
    content: str
    timestamp: str

# In-memory "database" (replace with real DB if needed)
current_prices = {}
strategy_news = []

# === API Endpoints ===

@app.get("/current-pricing")
def get_current_pricing():
    """Return the latest room prices"""
    return current_prices

@app.post("/update-pricing")
def update_pricing(price: PriceUpdate):
    """Update pricing info"""
    key = f"{price.date}_{price.room_type}"
    current_prices[key] = {
        "date": price.date,
        "room_type": price.room_type,
        "new_price": price.new_price,
        "reason": price.reason,
    }
    return {"status": "success", "message": "Pricing updated"}

@app.get("/strategy-news")
def get_strategy_news():
    """Return all strategy news items"""
    return strategy_news

@app.post("/add-strategy-news")
def add_strategy_news(news: StrategyNews):
    """Add a new strategy news item"""
    strategy_news.append(news.dict())
    return {"status": "success", "message": "News added"}

# === User Questions for Chatbot ===

class UserQuestion(BaseModel):
    question: str

@app.post("/user-question")
def answer_user_question(q: UserQuestion):
    """
    This endpoint will receive user questions.
    For now, it returns a dummy response.
    You can connect this to your LLM agent later.
    """
    # TODO: Connect with your LLM agent to generate an answer
    dummy_answer = f"Sorry, I can't answer '{q.question}' yet. This will be integrated soon."
    return {"answer": dummy_answer}
