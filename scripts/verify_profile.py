import os
import requests
import time
from dotenv import load_dotenv

# Load .env (same path logic as main.py)
load_dotenv(".env") 

BASE = "http://localhost:5000/api"
ADMIN_BASE = f"{BASE}/admin"
CHAT_BASE = f"{BASE}/chat"
PWD = os.getenv("ADMIN_PASSWORD", "secret-password")

def verify_profile_flow():
    print("1. Updating Profile via Admin API...")
    # Change Hours to something unique
    new_hours = f"Weekdays 9am-5pm (Updated at {time.time()})"
    
    headers = {"X-Admin-Password": PWD}
    r = requests.put(f"{ADMIN_BASE}/clients/oceanbite_001", json={"opening_hours": new_hours}, headers=headers)
    
    if r.status_code != 200:
        print(f"   FAILED: Admin update failed {r.status_code}")
        return

    print("   SUCCESS: Updated hours in DB.")

    print("\n2. Querying Chatbot for 'hours'...")
    # Chatbot should return the NEW hours immediately
    r = requests.post(f"{CHAT_BASE}", json={
        "client_id": "oceanbite_001",
        "message": "opening hours"
    }, headers={"X-API-KEY": "KELEVERDO12345jesse"})
    
    data = r.json()
    reply = data.get("messages", [{}])[0].get("text", "")
    
    if new_hours in reply:
        print(f"   SUCCESS: Chatbot returned new hours: '{reply}'")
    else:
        print(f"   FAILED: Chatbot returned old/wrong reply: '{reply}'")

if __name__ == "__main__":
    verify_profile_flow()
