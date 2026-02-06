import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app.extensions import db
from app.models import Client, MenuEmbedding, MenuItem

def check():
    with app.app_context():
        client = Client.query.first()
        if not client:
            print("No clients found.")
            return

        print(f"Checking Client: {client.restaurant_name}")
        
        total_items = MenuItem.query.filter_by(client_id=client.id).count()
        
        # Join to filter embeddings by client
        embeddings_count = MenuEmbedding.query.join(MenuItem).filter(MenuItem.client_id == client.id).count()
        
        print(f"Total Menu Items: {total_items}")
        print(f"Total Embeddings: {embeddings_count}")
        
        if total_items > 0 and embeddings_count == 0:
            print("⚠️ Data exists but embeddings are missing. Run sync_embeddings.py")
        elif total_items == embeddings_count:
            print("✅ All items have embeddings.")
        else:
             print(f"⚠️ Gap detected: {total_items - embeddings_count} items missing embeddings.")

if __name__ == "__main__":
    check()
