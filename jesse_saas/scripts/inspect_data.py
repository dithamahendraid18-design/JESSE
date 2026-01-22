import sys
import os
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path)

from app import create_app
from app.models import Client

def inspect():
    app = create_app()
    with app.app_context():
        print("🔍 Inspecting Database Content...")
        
        client = Client.query.first()
        if not client:
            print("❌ No clients found.")
            return

        kb = client.knowledge_base
        print(f"👤 Client: {client.restaurant_name}")
        print("-" * 40)
        print(f"📌 flow_location (Column): '{kb.flow_location}'")
        print("-" * 40)
        print(f"📌 flow_contact: '{kb.flow_contact}'")
        print("-" * 40)
        print(f"📌 conversation_starters (JSON):")
        try:
            starters = json.loads(kb.conversation_starters)
            print(json.dumps(starters, indent=2))
        except:
            print(f"RAW (Error parsing JSON): {kb.conversation_starters}")

if __name__ == "__main__":
    inspect()
