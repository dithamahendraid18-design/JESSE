import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_service import AIService

class DummyObj:
    def __getattr__(self, name):
        return None

def test_params_propagation():
    print("🎛️ Testing AI Parameter Propagation (Temperature & Tokens)...")
    
    # 1. Mock Client & KB with SPECIFIC settings
    mock_client = DummyObj()
    mock_client.restaurant_name = "Param Test Cafe"
    
    mock_kb = DummyObj()
    mock_kb.ai_provider = 'mock' 
    mock_kb.ai_api_key = 'test-key'
    
    # TEST VALUES
    TEST_TEMP = 0.9
    TEST_TOKENS = 777
    
    mock_kb.temperature = TEST_TEMP
    mock_kb.max_tokens = TEST_TOKENS
    
    # 2. Patch DB for Menu (return empty to focus on params)
    MenuItemMock = MagicMock()
    MenuItemMock.query.filter_by.return_value.all.return_value = []
    
    with patch('app.services.ai_service.MenuItem', MenuItemMock):
        with patch('app.services.ai_service.requests.post') as mock_post:
            # Mock API response
            mock_response = MagicMock()
            mock_response.json.return_value = {'choices': [{'message': {'content': 'OK'}}]}
            mock_post.return_value = mock_response
            
            # EXECUTE
            print(f"   Input: Temperature={TEST_TEMP}, MaxTokens={TEST_TOKENS}")
            AIService.generate_smart_reply("Test Params", mock_client, mock_kb)
            
            # VERIFY
            args, kwargs = mock_post.call_args
            payload = kwargs['json']
            
            used_temp = payload.get('temperature')
            used_tokens = payload.get('max_tokens')
            
            print(f"   Used Payload: Temperature={used_temp}, MaxTokens={used_tokens}")
            
            if used_temp == TEST_TEMP:
                print("✅ Temperature Passed Correctly")
            else:
                print(f"❌ Temperature Mismatch! Expected {TEST_TEMP}, Got {used_temp}")

            if used_tokens == TEST_TOKENS:
                print("✅ Max Tokens Passed Correctly")
            else:
                print(f"❌ Max Tokens Mismatch! Expected {TEST_TOKENS}, Got {used_tokens}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            test_params_propagation()
        except Exception as e:
            print(f"❌ Error: {e}")
