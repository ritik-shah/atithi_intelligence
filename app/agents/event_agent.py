import json
from app.llm import ask_llm

def event_agent(events_df):
    prompt = f"""
You are an AI hotel event strategist.

Upcoming events:
{events_df.to_string(index=False)}

Flag any dates needing special attention.

Respond ONLY with JSON array of:

[
  {{
    "type": "flag_day",
    "date": "2017-09-12",
    "note": "Local festival"
  }},
  ...
]
"""
    raw = ask_llm(prompt)
    try:
        actions = json.loads(raw)
        if isinstance(actions, list):
            return actions
    except Exception as e:
        print("Event agent JSON parse error:", e)
        print("LLM output:", raw)
    return []
