import requests
import os

api_key = os.environ.get('HUGGINGFACE_API_KEY')

models = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "BAAI/bge-small-en-v1.5"
]

headers = {"Authorization": f"Bearer {api_key}"}

def test(model):
    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    print(f"Testing {model} at {url}...")
    try:
        resp = requests.post(url, headers=headers, json={"inputs": "Hello world", "options": {"wait_for_model": True}})
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! Response snippet:", str(resp.json())[:100])
            return True
        else:
            print("Error:", resp.text)
    except Exception as e:
        print(f"Exception: {e}")
    return False

if __name__ == "__main__":
    for m in models:
        if test(m):
            print(f"✅ Works: {m}")
            break
