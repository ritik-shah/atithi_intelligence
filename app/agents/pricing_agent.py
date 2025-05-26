import json
from app.llm import ask_llm
from app.data import CURRENT_BOOKINGS, TOTAL_ROOMS_PER_TYPE

def pricing_agent(forecast_df, current_prices, event_flags=None):
    if event_flags is None:
        event_flags = []

    # Format event flags for prompt
    event_flag_text = "\n".join(
        f"- {event['date']}: {event.get('note', 'Special attention required')}"
        for event in event_flags
    ) or "None."

    prompt = f"""
You are an AI hotel pricing strategist.

📅 Forecast data for the next 14 days:
{forecast_df.to_string(index=False)}

📌 Upcoming Event Flags:
{event_flag_text}

💰 Current base prices (USD):
{json.dumps(current_prices, indent=2)}

🏨 Current bookings:
{json.dumps(CURRENT_BOOKINGS, indent=2)}

🛏️ Total rooms per type:
{json.dumps(TOTAL_ROOMS_PER_TYPE, indent=2)}

🎯 TASK:
Suggest optimal price updates for each room type across the full 14-day forecast.

Each suggestion must include:
- the exact date (`YYYY-MM-DD`)
- a brief reason in the "note" field (e.g., 'High demand due to event', 'Low occupancy forecast', etc.)

🚨 IMPORTANT:
Respond ONLY with a valid JSON array — NO explanation, NO headings.

📝 FORMAT:

[
  {{
    "type": "update_price",
    "room_type": "Standard",
    "price": 1600,
    "note": "High weekend demand",
    "date": "2025-05-25"
  }},
  {{
    "type": "update_price",
    "room_type": "Deluxe",
    "price": 1900,
    "note": "Low occupancy forecast",
    "date": "2025-05-25"
  }}
]
"""

    raw = ask_llm(prompt)

    # Attempt to parse raw JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("⚠️ JSON parsing failed. Attempting to clean response...")
        try:
            start = raw.index('[')
            end = raw.rindex(']') + 1
            cleaned = raw[start:end]

            # Replace invalid trailing commas or fix common mistakes
            cleaned = cleaned.replace(',\n]', '\n]')
            return json.loads(cleaned)

        except Exception as e:
            print("❌ Pricing agent JSON parse failed completely.")
            print("Raw LLM output:\n", raw)
            print("Exception:", str(e))
            return []
