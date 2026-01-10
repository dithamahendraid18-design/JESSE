import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
API_BASE = "http://localhost:5000/api"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret-password")
CLIENT_ID = "oceanbite_001"

def run_verification():
    print("🚀 Verifying Chatbot Images...")
    
    # 1. Upload a dummy image
    print("1. Uploading Dummy Image...")
    dummy_path = "verify_chat.png"
    with open(dummy_path, "wb") as f:
        f.write(os.urandom(1024))
        
    img_url = None
    try:
        with open(dummy_path, "rb") as f:
            resp = requests.post(f"{API_BASE}/upload", files={"file": f}, headers={"X-Admin-Password": ADMIN_PASSWORD})
            if resp.status_code == 201:
                img_url = resp.json()["url"]
                print(f"✅ Uploaded Image: {img_url}")
            else:
                print(f"❌ Upload Failed: {resp.text}")
                return
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

    # 2. Update Client Profile with Image
    print("2. Updating Client Profile...")
    payload = {"profile_image_url": img_url}
    resp = requests.put(f"{API_BASE}/admin/clients/{CLIENT_ID}", json=payload, headers={"X-Admin-Password": ADMIN_PASSWORD})
    if resp.status_code != 200:
        print(f"❌ Client Update Failed: {resp.text}")
        return
    print("✅ Client Profile Updated")

    # 3. Test 'About Us' Intent (Should return image)
    print("3. Testing 'About Us' Intent...")
    chat_payload = {
        "client_id": CLIENT_ID,
        "message": "tell me about us" 
    }
    # Note: "about us" triggers "about_us" intent via regex
    resp_chat = requests.post(f"{API_BASE}/chat", json=chat_payload)
    data = resp_chat.json()
    
    messages = data.get("messages", [])
    # Validating we got an image message
    found_img = False
    for m in messages:
        if m.get("type") == "image" and m.get("url") == img_url:
            found_img = True
            break
            
    if found_img:
        print("✅ 'About Us' returned profile image!")
    else:
        print("❌ 'About Us' DID NOT return profile image.")
        print(json.dumps(messages, indent=2))

    # 4. Update Menu Item with Image
    # First get menu items to find one
    print("4. Getting Menu Items...")
    menu_resp = requests.get(f"{API_BASE}/admin/clients/{CLIENT_ID}/menu", headers={"X-Admin-Password": ADMIN_PASSWORD})
    menu_data = menu_resp.json()
    
    # Pick first item
    item_id = None
    item_name = None
    if menu_data and menu_data[0].get("items"):
        item = menu_data[0]["items"][0]
        item_id = item["id"]
        item_name = item["name"]
    
    if not item_id:
        print("❌ No menu items found to test.")
        return

    print(f"5. Updating Item '{item_name}' ({item_id}) with Image...")
    # PUT /menu-items/<id> (Note: route might be /admin/menu-items/<id> or similar, checking previous steps...)
    # In routes_admin.py: @bp.put("/menu-items/<item_id>")
    # So URL is /api/admin/menu-items/<id> ??? No, let's check routes_admin.py
    # Actually, let's just try /api/admin/menu-items/{item_id}
    
    item_payload = {"image_url": img_url}
    item_resp = requests.put(f"{API_BASE}/admin/menu-items/{item_id}", json=item_payload, headers={"X-Admin-Password": ADMIN_PASSWORD})
    if item_resp.status_code != 200:
         # Tried standard guess, might be nested or different. 
         # Checked logs: `PUT /api/admin/menu-items/${id}` in admin.js
         print(f"❌ Item Update Failed: {item_resp.text}")
         return
    print("✅ Menu Item Updated")

    # 5. Test Menu Search (Should return image)
    print(f"6. Testing Search for '{item_name}'...")
    chat_payload["message"] = item_name
    # Force regex to NOT match menu/order so it falls through to search (if Pro plan)
    # OceanBite might be Basic or Pro. "oceanbite_001" is likely basic?
    # Wait, smart_search_menu is only for PRO.
    # Let's check plan type.
    client_check = requests.get(f"{API_BASE}/greeting?client_id={CLIENT_ID}").json()
    if client_check.get("plan_type") != "pro":
        print(f"⚠️ Plan is '{client_check.get('plan_type')}'. Search test might fail or skipped if not Pro.")
        # We can simulate Pro logic if we had access or just skip
    else:
        resp_search = requests.post(f"{API_BASE}/chat", json=chat_payload)
        search_msgs = resp_search.json().get("messages", [])
        
        found_item_img = False
        for m in search_msgs:
            if m.get("type") == "image" and m.get("url") == img_url:
                found_item_img = True
                break
        
        if found_item_img:
             print(f"✅ Search result for '{item_name}' returned image!")
        else:
             print(f"❌ Search result did NOT return image.")
             print(json.dumps(search_msgs, indent=2))

if __name__ == "__main__":
    run_verification()
