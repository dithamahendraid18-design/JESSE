
import sys
import os

# Ensure app path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app.services.vector_service import VectorService

def test_hf():
    print("Testing HF Embedding API...")
    with app.app_context():
        api_key = os.environ.get('HUGGINGFACE_API_KEY')
        print(f"API Key present: {bool(api_key)}")
        if api_key:
            print(f"Key starts with: {api_key[:4]}...")
        
        text = "This is a test menu item."
        vector = VectorService.get_embedding(text, api_key)
        
        if vector:
            print(f"✅ Success! Vector length: {len(vector)}")
            print(f"Sample: {vector[:5]}...")
        else:
            print("❌ Failed to get embedding.")

if __name__ == "__main__":
    test_hf()
