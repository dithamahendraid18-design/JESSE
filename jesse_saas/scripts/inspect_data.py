
import sys
import os
from sqlalchemy import text

# Ensure app path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app.extensions import db
from app.models import Client, MenuItem, MenuEmbedding
from app.services.vector_service import VectorService

def inspect_data():
    with app.app_context():
        print("--- Inspecting Database for AI Data ---")
        
        # Check Clients
        clients = Client.query.all()
        print(f"Total Clients: {len(clients)}")
        
        for client in clients:
            print(f"\n[Client: {client.restaurant_name} (ID: {client.id})]")
            
            # Check Menu Items
            menu_items = MenuItem.query.filter_by(client_id=client.id).all()
            print(f"  - Menu Items: {len(menu_items)}")
            
            # Check Embeddings
            embeddings_count = 0
            if menu_items:
                item_ids = [item.id for item in menu_items]
                embeddings = MenuEmbedding.query.filter(MenuEmbedding.menu_item_id.in_(item_ids)).all()
                embeddings_count = len(embeddings)
            print(f"  - Embeddings: {embeddings_count}")
            
            if len(menu_items) > 0 and embeddings_count == 0:
                print("  ⚠️ WARNING: Menu Items exist but NO EMBEDDINGS found! RAG will fail.")
                
            # Test Search
            if embeddings_count > 0:
                print("  - Testing Search 'menu'...")
                try:
                    results = VectorService.search_menu(client.id, "menu", limit=3)
                    if results:
                        print(f"    ✅ found {len(results)} items:")
                        for r in results:
                            print(f"      - {r.name} (${r.price})")
                    else:
                        print("    ❌ Search returned 0 results.")
                except Exception as e:
                    print(f"    ❌ Search Error: {e}")
            else:
                 print("  - Skipping search test (no embeddings).")

if __name__ == "__main__":
    inspect_data()
