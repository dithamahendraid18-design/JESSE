import requests
import json
import os
import uuid

from dotenv import load_dotenv

load_dotenv()
API_BASE = "http://localhost:5000/api"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret-password")
API_KEY = os.getenv("GLOBAL_API_KEY")
CLIENT_ID = "oceanbite_001"

def run():
    print("🔹 Verifying About Us Carousel...")
    
    # 1. Create a Card
    print("1. Creating About Card...")
    card_title = f"Test Card {uuid.uuid4().hex[:4]}"
    resp = requests.post(
        f"{API_BASE}/admin/clients/{CLIENT_ID}/about-cards",
        json={
            "image_url": "/uploads/test_card.jpg",
            "title": card_title,
            "description": "This is a verification card."
        },
        headers={"X-Admin-Password": ADMIN_PASSWORD}
    )
    if resp.status_code != 201:
        print(f"❌ Failed to create card: {resp.text}")
        return
    card_id = resp.json()["card"]["id"]
    print(f"✅ Card Created: ID {card_id}")

    # 2. Verify via Chat
    print("2. Checking Chat Response...")
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
        
    resp = requests.post(f"{API_BASE}/chat", json={
        "client_id": CLIENT_ID,
        "message": "about us"
    }, headers=headers)
    data = resp.json()
    
    # Check for carousel
    carousel = next((m for m in data.get("messages", []) if m.get("type") == "carousel"), None)
    if carousel:
        print("✅ Carousel Found in Response!")
        items = carousel.get("items", [])
        found = any(i["title"] == card_title for i in items)
        if found:
            print(f"✅ Found our card '{card_title}' in carousel items.")
        else:
            print(f"❌ Created card '{card_title}' NOT found in carousel items: {items}")
    else:
        print("❌ 'about_us' did NOT return a carousel!")
        # print(json.dumps(data, indent=2))
        return # Skip cleanup to debug

    # 3. Cleanup
    print("3. Deleting Card...")
    requests.delete(f"{API_BASE}/admin/about-cards/{card_id}", headers={"X-Admin-Password": ADMIN_PASSWORD})
    print("✅ Cleanup Done.")

if __name__ == "__main__":
    run()
