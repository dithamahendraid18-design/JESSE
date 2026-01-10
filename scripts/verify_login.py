import requests

BASE = "http://localhost:5000/api/admin"

def test_login():
    print("1. Trying Login with WRONG password...")
    r = requests.post(f"{BASE}/login", json={"password": "wrong-password"})
    if r.status_code == 401:
        print("   SUCCESS: Rejected (401)")
    else:
        print(f"   FAILED: Got {r.status_code}")

    print("\n2. Trying Login with CORRECT password...")
    # Default is "secret-password" if env not set
    r = requests.post(f"{BASE}/login", json={"password": "secret-password"})
    if r.status_code == 200:
        print("   SUCCESS: Logged in!")
        print(f"   Response: {r.json()}")
    else:
        print(f"   FAILED: Got {r.status_code} {r.text}")

    print("\n3. Accessing Protected Route with Password...")
    headers = {"X-Admin-Password": "secret-password"}
    r = requests.get(f"{BASE}/clients", headers=headers)
    if r.status_code == 200:
         print(f"   SUCCESS: Got {len(r.json())} clients")
    else:
         print(f"   FAILED: Got {r.status_code}")

if __name__ == "__main__":
    test_login()
