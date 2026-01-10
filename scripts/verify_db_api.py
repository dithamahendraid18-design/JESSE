import requests
import sys

try:
    url = "http://localhost:5000/api/greeting"
    params = {"client_id": "oceanbite_001"}
    headers = {"x-api-key": "KELEVERDO12345jesse"}
    
    print(f"Requesting {url}...")
    r = requests.get(url, params=params, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        name = data.get("meta", {}).get("client", "Unknown")
        print(f"SUCCESS: Loaded client '{name}' from DB!")
        if name != "OceanBite Seafood Grill":
            print("WARNING: Name mismatch?")
    else:
        print(f"FAILED: {r.status_code}")
        print(r.text)

except Exception as e:
    print(f"ERROR: {e}")
