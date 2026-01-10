import requests

BASE = "http://localhost:5000/api/admin"

def test_login():
    print("1. Trying Login with DEFAULT password ('secret-password')...")
    # If .env is loaded, this should FAIL (401) assuming user changed it in .env
    r = requests.post(f"{BASE}/login", json={"password": "secret-password"})
    
    if r.status_code == 401:
        print("   SUCCESS COMPLETED: Default password was REJECTED. This means .env IS loaded!")
    elif r.status_code == 200:
        print("   WARNING: Login SUCCEEDED with default password. .env might NOT be loaded (or user kept default).")
    else:
        print(f"   FAILED: Got {r.status_code} {r.text}")

if __name__ == "__main__":
    test_login()
