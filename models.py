# models.py
from pydantic import BaseModel
from typing import List
from datetime import date

# Room data for a single day
class RoomData(BaseModel):
    date: date
    room_type: str
    base_price: float
    updated_price: float
    price_change_pct: float
    booked_rooms: int
    available_rooms: int
    total_rooms: int = 20  # assuming fixed

# Staffing info for a single day
class StaffData(BaseModel):
    date: date
    staff_total: int
    staff_on_duty: int
    staff_off_duty: int
