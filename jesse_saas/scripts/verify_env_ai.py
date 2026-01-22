import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_service import AIService

def test_env_fallback():
    print("Testing AIService ENV Fallback Logic...")

    # Mock Client
    mock_client = MagicMock()
    mock_client.restaurant_name = "Env Test Bistro"
    
    # Mock KB with EMPTY AI settings
    mock_kb = MagicMock()
    mock_kb.ai_provider = None
    mock_kb.ai_model = None
    mock_kb.ai_api_key = None
    mock_kb.system_prompt = None
    mock_kb.temperature = None
    mock_kb.max_tokens = None
    
    # Mock KB Content
    mock_kb.about_us = "Env fallback testing."
    mock_kb.opening_hours = None
    mock_kb.location_address = None
    mock_kb.wifi_password = None
    mock_kb.contact_phone = None
    mock_kb.menu_url = None
    mock_kb.reservation_url = None
    mock_kb.payment_methods = None
    mock_kb.parking_info = None
    mock_kb.dietary_info = None
    mock_kb.policy_info = None

    # Set Environment Variables to match User's .env style
    os.environ['LLM_PROVIDER'] = 'openai_compatible'
    os.environ['LLM_BASE_URL'] = 'https://custom.groq.dev/v1' 
    os.environ['LLM_API_KEY'] = 'env-api-key-123'
    os.environ['LLM_MODEL'] = 'env-model-v2'

    print("\n1. Testing 'openai_compatible' logic from ENV...")
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Env Fallback Response'}}]
        }
        mock_post.return_value = mock_response
        
        reply = AIService.generate_smart_reply("Hello Env", mock_client, mock_kb)
        print(f"   Result: {reply}")
        
        # Verify Call
        args, kwargs = mock_post.call_args
        called_url = args[0]
        
        # Check URL construction
        assert called_url == "https://custom.groq.dev/v1/chat/completions"
        print("   ✅ URL Constructed Correctly (from LLM_BASE_URL)")
        
        # Check Auth
        assert kwargs['headers']['Authorization'] == "Bearer env-api-key-123"
        print("   ✅ API Key Used (from LLM_API_KEY)")
        
        # Check Model
        assert kwargs['json']['model'] == "env-model-v2"
        print("   ✅ Model Used (from LLM_MODEL)")

    # Cleanup
    del os.environ['LLM_PROVIDER']
    del os.environ['LLM_BASE_URL']
    del os.environ['LLM_API_KEY']
    del os.environ['LLM_MODEL']

if __name__ == "__main__":
    try:
        test_env_fallback()
        print("\n🎉 Environment Fallback Tests Passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
