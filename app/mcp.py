from app.data import forecast, events, sentiment, BASE_PRICES, latest_strategy
from app.agents import pricing_agent, staffing_agent, event_agent
import pandas as pd
from datetime import date, datetime
from supabase import create_client
import json

# Initialize Supabase
SUPABASE_URL = "https://tbycuaukgbqhusmayzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRieWN1YXVrZ2JxaHVzbWF5emNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5MjIyMzYsImV4cCI6MjA2MzQ5ODIzNn0.k-rs3SJ0XaneQjdc1eK-eI5U18cFfdAc3kjNI_yxTJ4"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Error check utility
def is_supabase_error(resp):
    if hasattr(resp, "error") and resp.error:
        return True, resp.error
    if hasattr(resp, "status_code") and resp.status_code >= 400:
        return True, f"HTTP status {resp.status_code}"
    return False, None

# ✅ Pricing insert
def upsert_pricing(price_changes):
    if not price_changes:
        print("⚠️ No pricing changes to insert.")
        return

    records = []
    for p in price_changes:
        if not p.get("date") or not p.get("room_type") or p.get("new_price") is None or p.get("base_price") is None:
            print(f"⚠️ Skipping invalid record: {p}")
            continue

        records.append({
            "date": p.get("date"),
            "room_type": p.get("room_type"),
            "base_price": p.get("base_price"),
            "new_price": p.get("new_price"),
            "change_pct": p.get("change_pct", 0),
            "note": p.get("note", "N/A"),
            "source": "agentic_ai"
        })

    # resp = supabase.table("pricing_history").insert(records).execute()
    resp = supabase.table("pricing_history").upsert(records, on_conflict="date,room_type").execute()
    error, msg = is_supabase_error(resp)
    print("✅ Supabase pricing insert:" if not error else f"❌ Pricing insert error: {msg}")

# ✅ Staffing insert
def upsert_staffing(staffing_changes):
    if not staffing_changes:
        print("⚠️ No staffing changes to insert.")
        return

    records = []
    for s in staffing_changes:
        staff_on_duty = s.get("staff_count")
        if staff_on_duty is None:
            print(f"⚠️ Skipping staffing record missing 'staff_count': {s}")
            continue
        date_val = s.get("date") or datetime.utcnow().date().isoformat()
        records.append({
            "date": date_val,
            "staff_on_duty": staff_on_duty,
            "note": s.get("note", "N/A"),
            "source": "agentic_ai",
            "staff_total": staff_on_duty + 2,  # Dummy logic
            "staff_off_duty": 2               # Dummy logic
        })

    if not records:
        print("⚠️ No valid staffing records to insert after filtering.")
        return

    resp = supabase.table("staffing_log").upsert(records, on_conflict=["date"]).execute()
    error, msg = is_supabase_error(resp)
    print("✅ Supabase staffing insert:" if not error else f"❌ Staffing insert error: {msg}")

# ✅ Event flags insert
def upsert_event_flags(event_actions):
    if not event_actions:
        print("⚠️ No event flags to insert.")
        return

    records = []
    for e in event_actions:
        date_val = e.get("date") or datetime.utcnow().date().isoformat()
        note_val = e.get("note") or e.get("details") or "No details provided"
        records.append({
            "date": date_val,
            "note": note_val,
            "source": "agentic_ai"
        })

    resp = supabase.table("event_flags").upsert(records, on_conflict="date").execute()
    error, msg = is_supabase_error(resp)
    print("✅ Supabase event_flags insert:" if not error else f"❌ Event flags insert error: {msg}")
def upsert_strategy_log(strategy_data):
    if not strategy_data:
        print("⚠️ No strategy data to insert.")
        return

    record = {
        "timestamp": strategy_data.get("timestamp"),
        "summary": strategy_data.get("summary"),
        "risk": strategy_data.get("risk"),
        "pricing_json": json.dumps(strategy_data.get("pricing_json", []), indent=2, sort_keys=True),
        "actions_json": json.dumps(strategy_data.get("actions_json", []), indent=2, sort_keys=True),
    }
    # print("🔍 strategy_data:", strategy_data)

    resp = supabase.table("strategy_log").insert(record).execute()
    error, msg = is_supabase_error(resp)
    print("✅ Supabase strategy_log insert:" if not error else f"❌ strategy_log insert error: {msg}")


# ✅ Main logic runner
def run_mcp(target_date: date = date(2017, 9, 8)):
    print(f"\n🚦 MCP started for {target_date.isoformat()}")

    # Step 1: Get event actions early
    event_actions = event_agent.event_agent(events)

    # Step 2: Extract just the flags for pricing and staffing agents
    event_flags = [
        {
            "date": e.get("date") or target_date.isoformat(),
            "note": e.get("details", "No details provided")
        } for e in event_actions
    ]

    # Step 3: Build occupancy forecast (booking surge) as percentage capacity from forecast data
    # Example assumes forecast is a DataFrame with 'date' and 'booked_rooms' columns
    # and total rooms available is known (adjust TOTAL_ROOMS accordingly)
    TOTAL_ROOMS = 100  # replace with actual total rooms available
    occupancy_forecast = {}
    if not forecast.empty:
        for _, row in forecast.iterrows():
            date_str = str(row.get("date") or target_date.isoformat())
            booked = row.get("booked_rooms", 0)
            occupancy_pct = (booked / TOTAL_ROOMS) * 100 if TOTAL_ROOMS else 0
            occupancy_forecast[date_str] = round(occupancy_pct, 2)

    # Step 4: Call pricing agent with event flags
    pricing_actions = pricing_agent.pricing_agent(forecast, BASE_PRICES, event_flags)

    # Step 5: Call staffing agent with enriched context: sentiment, base staffing, event flags, occupancy forecast
    staffing_actions = staffing_agent.staffing_agent(
        sentiment_df=sentiment,
        staff_on_duty=20,
        staff_total=30,
        event_flags=event_flags,
        occupancy_forecast=occupancy_forecast
    )
    print(f"DEBUG: staffing_actions = {staffing_actions}")
    # Ensure all actions have a date
    for action in staffing_actions + event_actions:
        if not action.get("date"):
            action["date"] = target_date.isoformat()

    all_actions = pricing_actions + staffing_actions + event_actions

    # Update BASE_PRICES with proposed pricing
    updated_prices = BASE_PRICES.copy()
    for action in pricing_actions:
        if action.get("type") == "update_price":
            room = action.get("room_type")
            price = action.get("price")
            if room in updated_prices and isinstance(price, (int, float)):
                updated_prices[room] = price

    # Build price_changes list
    price_changes = []
    for action in pricing_actions:
        if action.get("type") == "update_price":
            room = action.get("room_type")
            price = action.get("price")
            date_str = action.get("date")
            note = action.get("note", "")
            base_price = BASE_PRICES.get(room, 0)
            change_pct = ((price - base_price) / base_price) * 100 if base_price else 0

            price_changes.append({
                "room_type": room,
                "base_price": base_price,
                "new_price": price,
                "change_pct": round(change_pct, 2),
                "note": note,
                "date": date_str
            })

    # Risk summary
    avg_sentiment = sentiment["sentiment_score"].mean() if not sentiment.empty else 0
    risk = "⚠️ Negative sentiment trend" if avg_sentiment < 0 else "✅ Stable"

    summary = f"Pricing: {len(pricing_actions)} updates | Staffing: {len(staffing_actions)} | Events: {len(event_actions)}"
    latest_strategy.update({
        "timestamp": pd.Timestamp.now().isoformat(),
        "summary": summary,
        "pricing_json": price_changes,
        "actions_json": all_actions,
        "risk": risk
    })


    print(f"DEBUG: price_changes count: {len(price_changes)}")
    print(f"DEBUG: price_changes sample: {price_changes[:2]}")

    # Supabase inserts
    upsert_pricing(price_changes)
    upsert_staffing(staffing_actions)
    upsert_event_flags(event_actions)
    upsert_strategy_log(latest_strategy)

    print("\n📌 MODEL-DRIVEN CHANGES:")

    if price_changes:
        print("\n💰 Pricing Changes:")
        for p in price_changes:
            print(f"- [{p['date']}] {p['room_type']}: {p['base_price']} ➝ {p['new_price']} ({p['change_pct']}%) — {p['note']}")

    if staffing_actions:
        print("\n👥 Staffing Changes:")
        for s in staffing_actions:
            print(f"- [{s.get('date')}] Staff on duty: {s.get('staff_count')} — {s.get('note')}")

    if event_actions:
        print("\n📅 Event Flags:")
        for e in event_actions:
            print(f"- [{e.get('date')}] ⚠️ {e.get('note')}")

    # if latest_strategy and "actions_json" in latest_strategy:
        # print("\n📝 Strategy Actions:")
        # for action in latest_strategy["actions_json"]:
        #     action_type = action.get('type', 'unknown')
        #     date = action.get('date', 'N/A')
        #     note = action.get('note', '')
        
        # if action_type == 'update_price':
        #     room_type = action.get('room_type', 'N/A')
        #     price = action.get('price', 'N/A')
        #     print(f"- [{date}] 💲 Update price for {room_type}: ${price} ({note})")
        # elif action_type == 'adjust_staffing':
        #     staff_count = action.get('staff_count', 'N/A')
        #     print(f"- [{date}] 👥 Adjust staffing to {staff_count} ({note})")
        # elif action_type == 'flag_day':
        #     print(f"- [{date}] ⚠️ Flag Day: {note}")
        # else:
        #     print(f"- [{date}] 🔔 {action_type.capitalize()}: {note}")

        # print("\n📝 Strategy Actions:")
        # for action in latest_strategy:
        #     action_type = action.get('type', 'unknown')
        #     date = action.get('date', 'N/A')
        #     note = action.get('note', '')
        
        # # For price update actions
        # if action_type == 'update_price':
        #     room_type = action.get('room_type', 'N/A')
        #     price = action.get('price', 'N/A')
        #     print(f"- [{date}] 💲 Update price for {room_type}: ${price} ({note})")
        
        # # For staffing adjustments
        # elif action_type == 'adjust_staffing':
        #     staff_count = action.get('staff_count', 'N/A')
        #     print(f"- [{date}] 👥 Adjust staffing to {staff_count} ({note})")
        
        # # For flag day or other flags
        # elif action_type == 'flag_day':
        #     print(f"- [{date}] ⚠️ Flag Day: {note}")
        
        # # Any other action types
        # else:
        #     print(f"- [{date}] 🔔 {action_type.capitalize()}: {note}")



    print("✅ MCP finished. Summary:", summary)
