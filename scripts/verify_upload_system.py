import requests
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load Environment
load_dotenv()
API_BASE = "http://localhost:5000/api"
UPLOAD_URL = f"{API_BASE}/upload"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret-password")

# Verification Steps
def run_verification():
    print("🚀 Starting Image Upload System Verification...")

    # 1. Create Dummy Image
    dummy_filename = "test_upload_verify.png"
    dummy_path = Path(dummy_filename)
    try:
        with open(dummy_path, "wb") as f:
            f.write(os.urandom(2048)) # 2KB random noise
        print("✅ Created dummy image file.")
    except Exception as e:
        print(f"❌ Failed to create dummy file: {e}")
        return

    uploaded_url = None
    
    # 2. Upload File (Logged in)
    print("\nAttempting Upload (Authenticated)...")
    try:
        with open(dummy_path, "rb") as f:
            files = {"file": f}
            headers = {"X-Admin-Password": ADMIN_PASSWORD}
            resp = requests.post(UPLOAD_URL, files=files, headers=headers)
        
        if resp.status_code == 201:
            data = resp.json()
            uploaded_url = data.get("url")
            print(f"✅ Upload Success! Status: 201. URL: {uploaded_url}")
        else:
            print(f"❌ Upload Failed. Status: {resp.status_code}. Response: {resp.text}")
            return
    except Exception as e:
        print(f"❌ Exception during upload: {e}")
        return

    # 3. Verify Response URL format
    if uploaded_url and uploaded_url.startswith("/uploads/"):
        print(f"✅ URL format is valid: {uploaded_url}")
    else:
        print(f"❌ Invalid URL format returned: {uploaded_url}")
        return

    # 4. Check File Existence on Disk
    # Extract filename from URL /uploads/xxxxx.png
    uploaded_filename = uploaded_url.split("/")[-1]
    server_uploads_dir = Path("uploads") # Relative to backend root
    file_on_disk = server_uploads_dir / uploaded_filename
    
    if file_on_disk.exists():
        print(f"✅ Verified file exists on disk: {file_on_disk.absolute()}")
    else:
        print(f"❌ File NOT found on disk at: {file_on_disk.absolute()}")
        return

    # 5. Retrieve File via Public URL
    print("\nAttempting Retrieval via HTTP...")
    try:
        full_url = f"http://localhost:5000{uploaded_url}"
        get_resp = requests.get(full_url)
        if get_resp.status_code == 200:
            print(f"✅ File Retrieved Successfully via HTTP! Size: {len(get_resp.content)} bytes")
        else:
            print(f"❌ Failed to retrieve file. Status: {get_resp.status_code}")
            return
    except Exception as e:
        print(f"❌ Exception during retrieval: {e}")
        return

    # Cleanup
    if dummy_path.exists():
        os.remove(dummy_path)
    print("\n✨ Verification Complete: System is fully operational.")

if __name__ == "__main__":
    run_verification()
