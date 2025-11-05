from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

from app.schemas.training import WeekPlanRequest


def generate_week_plan(request: WeekPlanRequest) -> List[dict]:
    start = request.start_date
    end = request.end_date
    plan: List[dict] = []

    weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    day = start
    while day <= end:
        weekday = day.strftime("%a")
        hours = float(request.available_hours_by_day.get(weekday, 0.0))
        if hours <= 0.0:
            session = {"date": day, "session": "Rest", "hours": 0.0}
        else:
            # Simple repetitive block pattern (can be replaced with sport-specific progression)
            if weekday in ("Tue", "Thu"):
                session_type = "Intensity"
            elif weekday in ("Sat",):
                session_type = "Long"
            else:
                session_type = "Endurance"
            session = {"date": day, "session": session_type, "hours": round(hours, 2)}

        plan.append(session)
        day = day + timedelta(days=1)

    return plan

