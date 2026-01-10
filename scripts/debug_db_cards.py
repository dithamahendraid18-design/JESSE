from jesse.orm import Client, AboutCard, db
from jesse.app import create_app
import os

def run():
    app = create_app()
    with app.app_context():
        client_id = "oceanbite_001"
        client = db.session.get(Client, client_id)
        if not client:
            print(f"Client {client_id} not found!")
            return

        print(f"Client: {client.name}")
        cards = db.session.query(AboutCard).filter_by(client_id=client_id).all()
        print(f"Direct Query Count: {len(cards)}")
        
        print(f"Relationship Count: {len(client.about_cards)}")
        
        for c in client.about_cards:
            print(f" - {c.title}: {c.image_url}")

if __name__ == "__main__":
    run()
