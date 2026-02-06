from app import create_app, db
from app.models import Client, MenuItem

app = create_app()
with app.app_context():
    print("--- Listing All Clients ---")
    clients = Client.query.all()
    for c in clients:
        print(f"ID: {c.id} | Name: '{c.restaurant_name}' | PublicID: '{c.public_id}' | Slug: '{c.slug}'")

    print("\n--- Checking Savory ---")
    # Try multiple lookups
    client = Client.query.filter_by(public_id='savory-haven-bistro').first()
    if not client:
        client = Client.query.filter_by(slug='savory-haven-bistro').first()
    
    if client:
        count = MenuItem.query.filter_by(client_id=client.id, is_available=True).count()
        print(f"Target Client: {client.restaurant_name}")
        print(f"Active Menu Items: {count}")
        
        items = MenuItem.query.filter_by(client_id=client.id, is_available=True).all()
        # Calculate context size roughly
        total_chars = sum([len(i.name) + len(str(i.price)) + len(i.description or '') + 50 for i in items])
        print(f"Est Menu Chars: {total_chars}")
        print(f"Est Menu Tokens: {int(total_chars / 4)}")
    else:
        print("Savory still not found via public_id/slug lookups.")
