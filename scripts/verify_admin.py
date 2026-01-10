import requests
import json

BASE = "http://localhost:5000/api/admin"
HEADERS = {"X-Admin-Password": "secret-password"}

def test_admin():
    print("1. Listing Clients...")
    r = requests.get(f"{BASE}/clients", headers=HEADERS)
    if r.status_code != 200:
        print(f"FAILED: {r.text}")
        return
    clients = r.json()
    print(f"   Found {len(clients)} clients: {[c['id'] for c in clients]}")
    
    if not clients:
        return

    cid = clients[0]["id"]
    print(f"\n2. Fetching Menu for {cid}...")
    r = requests.get(f"{BASE}/clients/{cid}/menu", headers=HEADERS)
    menu = r.json()
    print(f"   Found {len(menu)} categories")
    
    if not menu:
        return
        
    item_id = menu[0]["items"][0]["id"]
    old_price = menu[0]["items"][0]["price"]
    print(f"   Item {item_id} price: {old_price}")

    print(f"\n3. Updating Item {item_id}...")
    new_price = old_price + 1.0
    r = requests.put(f"{BASE}/menu-items/{item_id}", json={"price": new_price}, headers=HEADERS)
    if r.status_code == 200:
        print(f"   SUCCESS: Updated to {r.json()['item']['price']}")
    else:
        print(f"   FAILED: {r.text}")

    # Revert
    requests.put(f"{BASE}/menu-items/{item_id}", json={"price": old_price}, headers=HEADERS)
    print("   (Reverted price)")

if __name__ == "__main__":
    test_admin()
