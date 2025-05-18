from datetime import datetime

def calculate_penalty(due_date, return_date, daily_price):
    days_late = (return_date - due_date).days
    return round(days_late * daily_price * 1.5, 2) if days_late > 0 else 0
