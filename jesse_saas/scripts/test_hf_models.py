
import sys
import os
import requests

# Ensure app path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app

def test_models():
    api_key = os.environ.get('HUGGINGFACE_API_KEY')
    if not api_key:
        print("No API Key.")
        return

    models = [
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-mpnet-base-v2",
        "BAAI/bge-small-en-v1.5",
        "google-bert/bert-base-uncased"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": ["Hello world"], "options": {"wait_for_model": True}}

    print(f"Testing {len(models)} models with Key ending in ...{api_key[-4:]}")
    
    for model in models:
        for domain in ["https://api-inference.huggingface.co/models", "https://router.huggingface.co/hf-inference/models"]:
            url = f"{domain}/{model}"
            print(f"\nTesting {model} on {domain}...", flush=True)
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=20)
                print(f"Status: {resp.status_code}", flush=True)
                if resp.status_code == 200:
                    print("✅ WORKING", flush=True)
                    data = resp.json()
                    # Check format (list of floats or list of list of floats)
                    if isinstance(data, list):
                        dim = len(data) if isinstance(data[0], float) else len(data[0])
                        print(f"Dimension: {dim}", flush=True)
                else:
                    print(f"❌ FAILED: {resp.text[:200]}", flush=True)
            except Exception as e:
                print(f"❌ EXCEPTION: {e}", flush=True)

if __name__ == "__main__":
    test_models()
