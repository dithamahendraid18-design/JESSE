import sys
import os

# Ensure app path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app.extensions import db
from app.services.vector_service import VectorService
from app.models import Client

def sync_all():
    with app.app_context():
        clients = Client.query.all()
        print(f"Found {len(clients)} clients.")
        
        for client in clients:
            print(f"--- Syncing for {client.restaurant_name} ({client.public_id}) ---")
            success = VectorService.sync_menu_embeddings(client.id)
            if success:
                print("✅ Sync Success")
            else:
                print("❌ Sync Failed (Check API Keys)")

if __name__ == "__main__":
    sync_all()
