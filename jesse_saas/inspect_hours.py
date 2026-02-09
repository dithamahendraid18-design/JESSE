from app.extensions import db
from app.models import Client
from app import create_app
import json

app = create_app()

with app.app_context():
    client = Client.query.first()
    if client:
        print(f"Client: {client.restaurant_name} (ID: {client.id})")
        print(f"Timezone: {client.timezone}")
        print(f"Raw Operating Hours: {client.operating_hours}")
        
        try:
            if client.operating_hours:
                hours = json.loads(client.operating_hours)
                print("Parsed Hours:")
                print(json.dumps(hours, indent=2))
            else:
                print("Operating Hours is None or Empty")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print("No client found")
