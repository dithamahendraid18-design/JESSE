import json
import re
from pathlib import Path
from sqlalchemy import text
from jesse.app import create_app
from jesse.database import db
from jesse.orm import Client

def extract_content(responses: dict, intent: str) -> str:
    """Helper to extract text content from responses.json structure."""
    data = responses.get("intents", {}).get(intent, {})
    
    # Try 'reply' field first (simple string)
    if "reply" in data:
        return data["reply"]
        
    # Try 'messages' array (first text message)
    messages = data.get("messages", [])
    for m in messages:
        if m.get("type") == "text":
            return m.get("text", "")
            
    return ""

def migrate():
    app = create_app()
    with app.app_context():
        print("Migrating Client Info from responses.json...")
        
        # 1. Add columns if not exist (SQLite safe check)
        with db.engine.connect() as conn:
            columns = ["address", "opening_hours", "contact_info", "description"]
            for col in columns:
                try:
                    conn.execute(text(f"ALTER TABLE clients ADD COLUMN {col} TEXT"))
                    print(f"Added column: {col}")
                except Exception as e:
                    print(f"Column {col} likely exists (skipping)")

        db.session.commit()

        # 2. Populate data
        clients_dir = app.config["SETTINGS"].clients_dir
        updates = 0
        
        for client_folder in clients_dir.iterdir():
            if not client_folder.is_dir(): continue
            
            client_id = client_folder.name
            responses_path = client_folder / "assets" / "responses.json"
            
            if not responses_path.exists():
                print(f"Skipping {client_id} (no responses.json)")
                continue

            try:
                with open(responses_path, "r", encoding="utf-8") as f:
                    responses = json.load(f)
                
                # Extract data using heuristics
                # Address -> 'location' intent
                address_full = extract_content(responses, "location")
                address = address_full # Ideally parse it, but full text is fine for now
                
                # Hours -> 'hours' intent
                hours = extract_content(responses, "hours")
                
                # Contact -> 'contact' intent
                contact = extract_content(responses, "contact")
                
                # Description -> 'about_us' intent
                desc = extract_content(responses, "about_us")

                # Update DB
                client = db.session.query(Client).get(client_id)
                if client:
                    client.address = address
                    client.opening_hours = hours
                    client.contact_info = contact
                    client.description = desc
                    updates += 1
                    print(f"Updated {client_id}")
                else:
                    print(f"Client {client_id} not found in DB")

            except Exception as e:
                print(f"Error processing {client_id}: {e}")
        
        db.session.commit()
        print(f"Migration Complete. Updated {updates} clients.")

if __name__ == "__main__":
    migrate()
