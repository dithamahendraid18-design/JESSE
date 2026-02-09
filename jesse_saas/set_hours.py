from app.extensions import db
from app.models import Client
from app import create_app
import json

app = create_app()

default_hours = {
    "monday": {"is_closed": False, "shifts": [{"start": "09:00", "end": "22:00"}]},
    "tuesday": {"is_closed": False, "shifts": [{"start": "09:00", "end": "22:00"}]},
    "wednesday": {"is_closed": False, "shifts": [{"start": "09:00", "end": "22:00"}]},
    "thursday": {"is_closed": False, "shifts": [{"start": "09:00", "end": "22:00"}]},
    "friday": {"is_closed": False, "shifts": [{"start": "09:00", "end": "23:00"}]},
    "saturday": {"is_closed": False, "shifts": [{"start": "10:00", "end": "23:00"}]},
    "sunday": {"is_closed": False, "shifts": [{"start": "10:00", "end": "22:00"}]}
}

with app.app_context():
    client = Client.query.first()
    if client:
        print(f"Updating hours for: {client.restaurant_name}")
        client.operating_hours = json.dumps(default_hours)
        db.session.commit()
        print("Updated operating hours successfully.")
    else:
        print("No client found")
