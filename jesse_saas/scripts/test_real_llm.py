import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env from project root (jesse_saas/scripts/../../.env)
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path)

from app.services.ai_service import AIService
class DummyObj:
    def __getattr__(self, name):
        return None

def test_real_connection():
    print("🤖 JESSE LLM Connection Tester")
    print("==============================")
    
    # Check Env Vars
    provider = os.environ.get('LLM_PROVIDER', 'groq')
    base_url = os.environ.get('LLM_BASE_URL', 'Default')
    model = os.environ.get('LLM_MODEL', 'Default')
    api_key = os.environ.get('LLM_API_KEY') or os.environ.get('GROQ_API_KEY')
    
    print(f"配置文件 (.env): {dotenv_path}")
    print(f"Provider    : {provider}")
    print(f"Base URL    : {base_url}")
    print(f"Model       : {model}")
    print(f"API Key     : {'*' * 8 + api_key[-4:] if api_key else 'NOT FOUND ❌'}")
    
    if not api_key:
        print("\n❌ Error: No API Key found in .env!")
        return

    print("\nAttempting to connect...")
    
    # Mock minimal Client/KB context
    mock_client = DummyObj()
    mock_client.restaurant_name = "Connection Test Cafe"
    
    mock_kb = DummyObj()
    # Explicitly ensure AI settings are None to trigger Env Fallback
    mock_kb.ai_provider = None 
    mock_kb.ai_api_key = None
    mock_kb.ai_model = None
    mock_kb.system_prompt = None

    try:
        reply = AIService.generate_smart_reply("Say 'Connection Successful' if you can hear me.", mock_client, mock_kb)
        print(f"\n💬 Response from LLM:\n---------------------\n{reply}\n---------------------")
        
        if "System Error" in reply or "trouble connecting" in reply:
             print("\n❌ Connectivity Issue Detected.")
        else:
             print("\n✅ Connection Successful!")
             
    except Exception as e:
        print(f"\n❌ Critical Error: {str(e)}")

if __name__ == "__main__":
    test_real_connection()
