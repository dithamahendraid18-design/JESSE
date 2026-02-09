from app.services.client_manager import ClientManager
from app.models import Client
from app import create_app
import json

app = create_app()

with app.app_context():
    # Create a dummy client to test defaults
    print("Creating test client...")
    client = ClientManager.create_client(
        restaurant_name="Test Defaults Resto",
        plan_type="basic"
    )
    
    print(f"Client Created: {client.restaurant_name} (ID: {client.id})")
    
    if client.operating_hours:
        hours = json.loads(client.operating_hours)
        print("Operating Hours found:")
        print(json.dumps(hours, indent=2))
        
        # Verify specific day
        if "monday" in hours and not hours["monday"]["is_closed"]:
            print("SUCCESS: Monday is open by default.")
        else:
            print("FAILURE: Monday default is incorrect.")
    else:
        print("FAILURE: Operating Hours is None.")
        
    # Cleanup
    from app.extensions import db
    db.session.delete(client)
    db.session.commit()
    print("Test client deleted.")
