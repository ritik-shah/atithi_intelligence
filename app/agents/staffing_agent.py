import json
from app.llm import ask_llm

def staffing_agent(sentiment_df, staff_on_duty, staff_total, event_flags=None, occupancy_forecast=None):
    event_block = ""
    if event_flags:
        event_lines = [f"- {e['date']}: {e['note']}" for e in event_flags]
        event_block = "\n📌 Event Flags:\n" + "\n".join(event_lines)

    surge_block = ""
    if occupancy_forecast:
        surge_lines = [f"- {date}: {occupancy}%" for date, occupancy in occupancy_forecast.items()]
        surge_block = "\n📈 Booking Surge:\n" + "\n".join(surge_lines)

    prompt = f"""
You are an AI hotel staffing strategist.

Sentiment data:
{sentiment_df.to_string(index=False)}

Current staff on duty: {staff_on_duty}
Total staff: {staff_total}

{event_block}
{surge_block}

Suggest adjustments to daily staffing based on guest sentiment, booking surge, and special events.

Respond ONLY with a JSON array (no extra text, no explanation), exactly like:

[
  {{
    "type": "adjust_staffing",
    "date": "2017-09-10",
    "staff_count": 22,
    "note": "Increase due to demand"
  }}
]

Your response MUST be valid JSON parsable by Python json.loads().
"""

    raw = ask_llm(prompt)

    import re
    def extract_json(raw_text):
        match = re.search(r'(\[\s*\{.*\}\s*\])', raw_text, re.DOTALL)
        if match:
            return match.group(1)
        return raw_text

    try:
        json_text = extract_json(raw)
        actions = json.loads(json_text)
        if isinstance(actions, list):
            return actions
    except Exception as e:
        print("Staffing agent JSON parse error:", e)
        print("LLM output:", raw)
    return []

