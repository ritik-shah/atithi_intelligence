# generate_mock_data.py
import json
from datetime import datetime, timedelta
from models import RoomData, StaffData
from constants import room_types

start_date = datetime.strptime("2017-09-08", "%Y-%m-%d")
num_days = 14
room_records = []
staff_records = []

# === Generate data ===
for i in range(num_days):
    current_date = (start_date + timedelta(days=i)).date()

    # For each room type
    for room_type, base_price in room_types.items():
        # Random fluctuations for bookings and prices
        booked = max(0, min(20, 10 + i % 5 + (hash(room_type + str(i)) % 5 - 2)))
        available = 20 - booked
        price_multiplier = 1 + ((hash(room_type + str(current_date)) % 10 - 5) / 100)
        updated_price = round(base_price * price_multiplier)
        price_change_pct = round(((updated_price - base_price) / base_price) * 100, 2)

        room = RoomData(
            date=current_date,
            room_type=room_type,
            base_price=base_price,
            updated_price=updated_price,
            price_change_pct=price_change_pct,
            booked_rooms=booked,
            available_rooms=available
        )
        room_records.append(room.dict())

    # Staff data
    total_staff = 25
    on_duty = 15 + i % 4
    off_duty = total_staff - on_duty

    staff = StaffData(
        date=current_date,
        staff_total=total_staff,
        staff_on_duty=on_duty,
        staff_off_duty=off_duty
    )
    staff_records.append(staff.dict())

# === Write to JSON files ===
with open("hotel_data/hotel_rooms.json", "w") as f:
    json.dump(room_records, f, indent=2, default=str)

with open("hotel_data/hotel_staff.json", "w") as f:
    json.dump(staff_records, f, indent=2, default=str)

print("✅ Mock data generated successfully.")
