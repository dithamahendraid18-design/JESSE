
import sys
import os
import requests

# Ensure app path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app

def test_router():
    api_key = os.environ.get('HUGGINGFACE_API_KEY')
    model = "sentence-transformers/all-MiniLM-L6-v2"
    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Try different payloads
    payloads = [
        {"inputs": "Hello world", "options": {"wait_for_model": True}},
        {"inputs": ["Hello world"], "options": {"wait_for_model": True}}
    ]
    
    print(f"Testing Router: {url}")
    
    for i, p in enumerate(payloads):
        print(f"\nPayload {i}: {p}")
        try:
            resp = requests.post(url, headers=headers, json=p, timeout=20)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_router()
