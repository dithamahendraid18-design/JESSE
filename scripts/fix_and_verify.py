import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
API_BASE = "http://localhost:5000/api"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret-password")
CLIENT_ID = "oceanbite_001"

def run():
    print("🔹 Fix and Verify Script")
    
    # 1. Update Profile Image
    img_url = "/uploads/manual_fix.png" 
    # (We pretend we uploaded this, just testing DB persistence)
    
    print(f"Updating {CLIENT_ID} with {img_url}...")
    resp = requests.put(
        f"{API_BASE}/admin/clients/{CLIENT_ID}", 
        json={"profile_image_url": img_url},
        headers={"X-Admin-Password": ADMIN_PASSWORD}
    )
    print(f"Update Resp: {resp.status_code} - {resp.text}")
    
    # 2. Check DB via API
    resp_get = requests.get(f"{API_BASE}/admin/clients", headers={"X-Admin-Password": ADMIN_PASSWORD})
    clients = resp_get.json()
    c = next((x for x in clients if x['id'] == CLIENT_ID), None)
    
    # Note: list_clients default response might NOT include profile_image_url if I didn't add it to list_clients serializer?
    # Let's check routes_admin.py:list_clients again?
    # Step 933:
    # data.append({ "id", "name", ... "description" }) 
    # IT DOES NOT INCLUDE "profile_image_url" in the list response!
    
    # Ah! So verify_chatbot_images.py might have failed to verify via admin list? 
    # No, verify_chatbot_images.py tested via CHAT intent.
    
    # But for this script, I'll check via CHAT intent.
    
    print("Checking via Chat 'About Us'...")
    resp_chat = requests.post(f"{API_BASE}/chat", json={
        "client_id": CLIENT_ID,
        "message": "about us"
    })
    print(json.dumps(resp_chat.json(), indent=2))

if __name__ == "__main__":
    run()
