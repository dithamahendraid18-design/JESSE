
import os
import requests
import shutil
from pathlib import Path

# Verify that we can run WITHOUT clients/ folder
# 1. Rename clients/ folder
# 2. Call API to get client detail
# 3. Restore folder

def run():
    print("🔹 FINAL MIGRATION VERIFICATION 🔹")
    clients_path = Path("clients")
    backup_path = Path("clients_backup")
    
    if clients_path.exists():
        print("Moving clients/ folder to clients_backup/ ...")
        try:
            # os.rename(clients_path, backup_path)
            # rename might fail if file locked, stick to copy/delete or just assume it is safe because we updated code?
            # Let's try rename.
            os.rename(clients_path, backup_path)
        except Exception as e:
            print(f"⚠️ Could not rename folder (maybe locked?): {e}")
            print("Proceeding anyway to test logic...")
    
    try:
        # TEST 1: Load Client (Admin)
        print("1. Testing GET /api/admin/clients...")
        headers = {"X-Admin-Password": os.getenv("ADMIN_PASSWORD", "secret-password")}
        resp = requests.get("http://localhost:5000/api/admin/clients", headers=headers)
        if resp.status_code == 200:
            print(f"✅ Clients List: Found {len(resp.json())} clients.")
        else:
            print(f"❌ Failed to list clients: {resp.status_code}")

        # TEST 2: Chat (Client Loader)
        print("2. Testing Chat (Bootloader)...")
        headers_chat = {}
        api_key = os.getenv("GLOBAL_API_KEY")
        if api_key: headers_chat["X-API-Key"] = api_key
        
        resp = requests.post("http://localhost:5000/api/chat", json={
            "client_id": "oceanbite_001",
            "message": "hello"
        }, headers=headers_chat)
        
        if resp.status_code == 200:
            print("✅ Chat successful (Client Loaded without file error).")
        else:
            print(f"❌ Chat failed: {resp.text}")

        # TEST 3: Check Migrated URLs (Admin API)
        print("3. Checking Migrated Asset URLs...")
        resp = requests.get("http://localhost:5000/api/admin/clients/oceanbite_001/about-cards", headers=headers)
        if resp.status_code == 200:
            cards = resp.json()
            if cards:
                url = cards[0]["image_url"]
                print(f"  First Card URL: {url}")
                if "/uploads/" in url or url.startswith("http"):
                    print("✅ Card URL migrated correctly.")
                else:
                    print(f"⚠️ Card URL might still be legacy: {url}")
            else:
                 print("  No cards to check.")
        else:
             print("❌ Failed to fetch about cards.")

    finally:
        # Restore
        if backup_path.exists():
            print("Restoring clients/ folder...")
            try:
                os.rename(backup_path, clients_path)
                print("Restored.")
            except:
                print("⚠️ Failed to restore clients folder.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
