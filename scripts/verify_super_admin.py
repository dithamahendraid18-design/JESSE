
import requests
import os
import uuid

# Load Env
# Make sure to call load_dotenv BEFORE accessing os.getenv
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:5000/api/admin"
# Hardcode default from config.py if env missing for test simplicity, 
# or better, print if missing.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    print("⚠️ ADMIN_PASSWORD not found in env, using default 'admin123'")
    ADMIN_PASSWORD = "admin123"

HEADERS = {"X-Admin-Password": ADMIN_PASSWORD}

def run():
    print("🔹 SUPER ADMIN FLOW VERIFICATION 🔹")
    
    unique_suffix = uuid.uuid4().hex[:6]
    slug = f"test_resto_{unique_suffix}"
    name = "Test Resto"

    # 1. Create Client
    print(f"1. Creating Client: {name} ({slug})...")
    resp = requests.post(f"{API_BASE}/clients", json={"name": name, "slug": slug}, headers=HEADERS)
    if resp.status_code == 201:
        print(f"✅ Created. ID: {resp.json().get('client_id')}")
    else:
        print(f"❌ Failed to create: {resp.text}")
        return

    # 2. Check Client List
    print("2. Verifying in Client List...")
    resp = requests.get(f"{API_BASE}/clients", headers=HEADERS)
    clients = resp.json()
    found = any(c['id'] == slug for c in clients)
    if found:
        print("✅ Client found in list.")
    else:
        print("❌ Client NOT found in list.")
        return

    # 3. Add Sub-resources (e.g. About Card) logic should be tested too?
    # Let's assume default menu items created by POST /clients logic are enough to test cascading delete.

    # 4. Delete Client
    print("3. Deleting Client...")
    resp = requests.delete(f"{API_BASE}/clients/{slug}", headers=HEADERS)
    if resp.status_code == 200:
        print("✅ Deleted successfully.")
    else:
        print(f"❌ Failed to delete: {resp.text}")
        return

    # 5. Verify Deletion (Accessing Menu should fail)
    print("4. Verifying Cascade Delete (Menu)...")
    resp = requests.get(f"{API_BASE}/clients/{slug}/menu", headers=HEADERS)
    if resp.status_code == 404:
        print("✅ Verified: Client menu not found (Cascade successful).")
    else:
        print(f"❌ WARNING: Client menu still accessible? Status: {resp.status_code}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
