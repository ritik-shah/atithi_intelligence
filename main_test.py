# main.py
from models import RoomData, StaffData
import json
from datetime import date

# Sample entry
room_entry = RoomData(
    date=date(2017, 9, 8),
    room_type="Deluxe",
    base_price=2000,
    updated_price=2100,
    price_change_pct=5.0,
    booked_rooms=12,
    available_rooms=8
)

# Write to JSON
with open("hotel_data/hotel_rooms.json", "w") as f:
    json.dump([room_entry.dict()], f, indent=2, default=str)
