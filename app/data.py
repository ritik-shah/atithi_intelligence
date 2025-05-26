import pandas as pd

# Load or fallback dummy data for demo
def load_forecast():
    try:
        return pd.read_json("forecast_output.json")
    except Exception:
        dates = pd.date_range("2025-05-25", periods=14)
        return pd.DataFrame({"ds": dates, "yhat": [150, 160, 170, 140, 130, 125, 155, 165, 180, 175, 160, 150, 140, 135]})

def load_events():
    try:
        return pd.read_csv("events.csv")
    except Exception:
        return pd.DataFrame(columns=["date", "event"])

def load_sentiment():
    try:
        return pd.read_csv("sentiment.csv")
    except Exception:
        dates = pd.date_range("2025-05-25", periods=14)
        return pd.DataFrame({"date": dates, "sentiment_score": [0.1, 0.2, -0.1, 0, 0.05, -0.2, 0.3, 0.1, -0.05, 0, 0.15, 0.2, 0.1, 0]})

# Global hotel data and state
BASE_PRICES = {
    "Standard": 1500,
    "Deluxe": 2000,
    "Suite": 2500,
    "Executive": 3000,
    "Presidential": 4000,
}

TOTAL_ROOMS_PER_TYPE = 20

CURRENT_BOOKINGS = {
    "Standard": 10,
    "Deluxe": 5,
    "Suite": 8,
    "Executive": 12,
    "Presidential": 6,
}

STAFF_TOTAL = 30
STAFF_ON_DUTY = 20
STAFF_OFF_DUTY = STAFF_TOTAL - STAFF_ON_DUTY

# Global state to store latest strategy and pricing
latest_strategy = {
    "timestamp": None,
    "summary": "",
    "pricing": [],
    "actions": [],
    "risk": ""
}

# Load data at module import
forecast = load_forecast()
events = load_events()
sentiment = load_sentiment()
