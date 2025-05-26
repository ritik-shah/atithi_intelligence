import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import random

# ==== CONFIG ====
SUPABASE_URL = "https://tbycuaukgbqhusmayzcl.supabase.co" # e.g. "https://xyzcompany.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRieWN1YXVrZ2JxaHVzbWF5emNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5MjIyMzYsImV4cCI6MjA2MzQ5ODIzNn0.k-rs3SJ0XaneQjdc1eK-eI5U18cFfdAc3kjNI_yxTJ4"  # Use service role key for inserts

# Initialize client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Base prices and constants
BASE_PRICES = {
    "Standard": 1500,
    "Deluxe": 2000,
    "Suite": 2500,
    "Executive": 3000,
    "Presidential": 4000,
}
TOTAL_ROOMS_PER_TYPE = 20

STAFF_TOTAL = 30
STAFF_ON_DUTY = 20
STAFF_OFF_DUTY = STAFF_TOTAL - STAFF_ON_DUTY

START_DATE = datetime.strptime("2025-05-25", "%Y-%m-%d")
DAYS = 180

def generate_pricing_data():
    pricing_data = []
    for day_offset in range(DAYS):
        date = (START_DATE + timedelta(days=day_offset)).date().isoformat()
        for room_type, base_price in BASE_PRICES.items():
            # Randomly vary price by +/- 10%
            variation_pct = random.uniform(-0.1, 0.1)
            updated_price = int(base_price * (1 + variation_pct))
            change_pct = round(variation_pct * 100, 2)

            pricing_data.append({
                "date": date,
                "room_type": room_type,
                "base_price": base_price,
                "new_price": updated_price,   # <-- changed here
                "change_pct": change_pct,
                "source": "mock_data_script"
            })
    return pricing_data


def generate_staff_data():
    staff_data = []
    for day_offset in range(DAYS):
        date = (START_DATE + timedelta(days=day_offset)).date().isoformat()
        # Randomly fluctuate staff on duty +/- 3 staff
        on_duty = max(10, min(STAFF_TOTAL, STAFF_ON_DUTY + random.randint(-3, 3)))
        off_duty = STAFF_TOTAL - on_duty

        staff_data.append({
            "date": date,
            "staff_total": STAFF_TOTAL,
            "staff_on_duty": on_duty,
            "staff_off_duty": off_duty,
            "source": "mock_data_script"
        })
    return staff_data

def chunk_list(data, chunk_size=50):
    for i in range(0, len(data), chunk_size):
        yield data[i:i+chunk_size]

def main():
    pricing_data = generate_pricing_data()
    staff_data = generate_staff_data()

    print(f"Inserting {len(pricing_data)} pricing records...")
    for chunk in chunk_list(pricing_data):
        response = supabase.table("pricing_history").insert(chunk).execute()
        # Check for errors properly
        if getattr(response, "error", None):
            print("Error inserting pricing chunk:", response.error)
        else:
            inserted_count = len(getattr(response, "data", []))
            print(f"Inserted pricing chunk with {inserted_count} records")

    print(f"Inserting {len(staff_data)} staffing records...")
    for chunk in chunk_list(staff_data):
        response = supabase.table("staffing_log").insert(chunk).execute()
        if getattr(response, "error", None):
            print("Error inserting staffing chunk:", response.error)
        else:
            inserted_count = len(getattr(response, "data", []))
            print(f"Inserted staffing chunk with {inserted_count} records")

if __name__ == "__main__":
    main()
