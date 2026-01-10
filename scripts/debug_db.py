from jesse.app import create_app
from jesse.orm import Client, MenuItem

app = create_app()
with app.app_context():
    client = Client.query.get("oceanbite_001")
    if client:
        print(f"Client: {client.name}")
        print(f"Description: {client.description}")
        print(f"Profile Image: {client.profile_image_url}")
    else:
        print("Client not found")

    items = MenuItem.query.limit(5).all()
    for item in items:
        print(f"Item: {item.name}, ImageURL: {item.image_url}")
