from app import create_app
from app.services.ai_service import AIService
from app.models import Client, KnowledgeBase
import json
from datetime import datetime
import pytz

app = create_app()

with app.app_context():
    # Mock data structure matching User's scenario
    # "Monday to Thursday from 11:00 AM to 10:00 PM (22:00)"
    # "Friday to Sunday from 11:00 AM to 12:00 AM (00:00)"
    
    hours_data = {
        "monday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "22:00"}]},
        "tuesday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "22:00"}]},
        "wednesday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "22:00"}]},
        "thursday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "22:00"}]},
        "friday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "00:00"}]},
        "saturday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "00:00"}]},
        "sunday": {"is_closed": False, "shifts": [{"start": "11:00", "end": "00:00"}]}
    }
    
    # Mock Client & KB (We don't save to DB, just use objects if possible, 
    # but AIService takes models. We might need to mock attributes.)
    
    class MockClient:
        restaurant_name = "Debug Resto"
        operating_hours = json.dumps(hours_data)
        address = "123 Debug St"
        timezone = "Asia/Jakarta" # Assumption
        currency_code = "IDR"
        # ... other safe_get attributes
        public_phone = "123"
        public_email = "test@test.com"
        website_url = "google.com"
        
        # Add a dictionary for safe_get to work if it uses .get() or getattr
        def __getitem__(self, item):
            return getattr(self, item, None)
        def get(self, item, default=None):
            return getattr(self, item, default)

    class MockKB:
        about_us = "A cool place."
        holiday_dates = "[]"
        
        def __getitem__(self, item):
            return getattr(self, item, None)
        def get(self, item, default=None):
            return getattr(self, item, default)

    client = MockClient()
    kb = MockKB()
    client.knowledge_base = kb # Link them if needed, though generate_smart_reply separates them
    
    # We need to access the logic inside AIService that generates the prompt. 
    # Since generate_smart_reply is a big function that calls LLM, we should extract the prompt construction logic 
    # OR construct it manually here using the exact same logic as ai_service.py to verify.
    
    # Let's copy the logic from ai_service.py lines 166-179 (approx)
    operating_hours_text = "Open daily"
    try:
        op_hours = client.operating_hours
        hours_json = json.loads(op_hours or '{}')
        if isinstance(hours_json, dict) and len(hours_json) > 0:
            h_lines = []
            # Force order
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                data = hours_json.get(day)
                if data:
                    if data.get('is_closed'):
                        h_lines.append(f"- {day.capitalize()}: CLOSED")
                    else:
                        shifts = data.get('shifts', [])
                        formatted_shifts = []
                        for s in shifts:
                            start, end = s['start'], s['end']
                            if end == "00:00": end = "24:00 (Midnight)" # Explicit for AI
                            formatted_shifts.append(f"{start}-{end}")
                        shift_str = ", ".join(formatted_shifts)
                        h_lines.append(f"- {day.capitalize()}: {shift_str}")
            operating_hours_text = "\n".join(h_lines)
    except Exception as e:
        operating_hours_text = f"Error: {e}"

    print("--- GENERATED HOURS TEXT ---")
    print(operating_hours_text)
    print("----------------------------")
    
    # Now conversion logic check
    # AI sees 24h format. User report says AI outputs 12h format. 
    # This means AI is doing the translation.
    
    # Checking prompt "OPERATIONS" section context
    print("Prompt Context Check:")
    print(f"- **Hours:**\n{operating_hours_text}")
