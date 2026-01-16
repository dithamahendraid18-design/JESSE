from app import create_app
from app.models import Client

app = create_app()

with app.app_context():
    client = Client.query.first()
    if client:
        print(f"Public ID: {client.public_id}")
        print(f"Slug: {client.slug}")
    else:
        print("No clients found.")
