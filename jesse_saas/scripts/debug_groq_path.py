import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path)

from app.services.ai_service import AIService

class DummyObj:
    def __getattr__(self, name):
        return None

def test_groq_path():
    print("🐞 Debugging 'Groq' Provider Path (DB Default)")
    print("============================================")
    
    # 1. Simulate DB State where provider is 'groq' (Default)
    mock_kb = DummyObj()
    mock_kb.ai_provider = 'groq'  # <--- EXACTLY what causes the difference
    mock_kb.ai_api_key = None     # User hasn't set specific key in dashboard
    mock_kb.ai_model = None       # Default model
    
    mock_client = DummyObj()
    mock_client.restaurant_name = "Debug Cafe"

    print(f"Provider: {mock_kb.ai_provider}")
    
    # Check what key usage matches ai_service logic
    # Logic: if provider=='groq', use GROQ_API_KEY or LLM_API_KEY
    expected_key = os.environ.get('GROQ_API_KEY') or os.environ.get('LLM_API_KEY')
    print(f"Expected Key: {'*' * 8 + expected_key[-4:] if expected_key else 'NONE'}")
    
    try:
        print("\nAttempting call via AIService._call_groq...")
        reply = AIService.generate_smart_reply("Hello Debug", mock_client, mock_kb)
        print(f"\nResponse: {reply}")
        
    except Exception as e:
        print(f"\n❌ CRASH: {e}")

if __name__ == "__main__":
    test_groq_path()
