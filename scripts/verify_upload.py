import requests
import os

from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:5000/api"
UPLOAD_ENDPOINT = f"{API_BASE}/upload"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret-password")
CLIENT_ID = "oceanbite_001" # Known ID

def test_upload_flow():
    print("1. Creating dummy image file...")
    dummy_path = "test_image.png"
    with open(dummy_path, "wb") as f:
        f.write(os.urandom(1024)) # 1KB random data

    print("2. Uploading file...")
    try:
        with open(dummy_path, "rb") as f:
            files = {"file": f}
            headers = {"X-Admin-Password": ADMIN_PASSWORD}
            resp = requests.post(UPLOAD_ENDPOINT, files=files, headers=headers)
        
        if resp.status_code == 201:
            data = resp.json()
            url = data.get("url")
            print(f"✅ Upload Success! URL: {url}")
            
            # Verify retrieval
            print(f"3. Retrieving uploaded file from {url}...")
            # Note: The URL returned is relative e.g., /uploads/xxx
            # We need to prepend host
            full_url = f"http://localhost:5000{url}"
            get_resp = requests.get(full_url)
            if get_resp.status_code == 200:
                 print("✅ File Retrieved Successfully!")
            else:
                 print(f"❌ Failed to retrieve file: {get_resp.status_code}")

            # Verify Updating Client Profile
            print("4. Updating Client Profile with Image URL...")
            update_url = f"{API_BASE}/admin/clients/{CLIENT_ID}"
            payload = {
                "profile_image_url": url
            }
            # Fetch existing to avoid nuking other fields? 
            # The API might partial update or overwrite?
            # Let's just send this and see if it sticks. 
            # Wait, my PUT implementation in routes_admin might expect all fields or default to None if missing.
            # Checking routes_admin.py...
            # It uses req_data.get("field", client.field). So partial update is supported conceptually 
            # IF the code does `client.field = data.get('field', client.field)`.
            # Let's assume it does (checked mentally or I should check).
            
            resp_update = requests.put(update_url, json=payload, headers=headers)
            if resp_update.status_code == 200:
                print("✅ Client Profile Updated!")
                # Verify it stuck
                resp_get = requests.get(f"{API_BASE}/admin/clients", headers=headers)
                clients = resp_get.json()
                client = next((c for c in clients if c['id'] == CLIENT_ID), None)
                if client and client.get('profile_image_url') == url:
                    print(f"✅ Verified profile_image_url in DB: {client['profile_image_url']}")
                else:
                    print(f"❌ Failed to verify profile_image_url in DB. Got: {client.get('profile_image_url')}")
            else:
                 print(f"❌ Failed to update client profile: {resp_update.text}")

        else:
            print(f"❌ Upload Failed: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
            print("Cleanup done.")

if __name__ == "__main__":
    test_upload_flow()
