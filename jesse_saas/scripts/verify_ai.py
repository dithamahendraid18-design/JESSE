import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_service import AIService

def test_ai_service_dispatch():
    print("Testing AIService Dispatch Logic...")

    # Mock Client and KB
    mock_client = MagicMock()
    mock_client.restaurant_name = "Test Bistro"
    
    mock_kb = MagicMock()
    mock_kb.about_us = "We are a test bistro."
    mock_kb.system_prompt = None # Test default generation
    mock_kb.ai_api_key = "sk-test-key"
    mock_kb.temperature = 0.5
    mock_kb.max_tokens = 100

    # Test Groq Dispatch
    print("\n1. Testing Groq Dispatch...")
    mock_kb.ai_provider = "groq"
    mock_kb.ai_model = "llama3-70b-8192"
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Groq Response'}}]
        }
        mock_post.return_value = mock_response
        
        reply = AIService.generate_smart_reply("Hello", mock_client, mock_kb)
        print(f"   Result: {reply}")
        
        # Verify Call
        args, kwargs = mock_post.call_args
        assert "api.groq.com" in args[0]
        assert kwargs['headers']['Authorization'] == "Bearer sk-test-key"
        assert kwargs['json']['model'] == "llama3-70b-8192"
        print("   ✅ Groq Call Verified")

    # Test OpenAI Dispatch
    print("\n2. Testing OpenAI Dispatch...")
    mock_kb.ai_provider = "openai"
    mock_kb.ai_model = "gpt-4o"
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'OpenAI Response'}}]
        }
        mock_post.return_value = mock_response
        
        reply = AIService.generate_smart_reply("Hello", mock_client, mock_kb)
        print(f"   Result: {reply}")
        
        # Verify Call
        args, kwargs = mock_post.call_args
        assert "api.openai.com" in args[0]
        assert kwargs['json']['model'] == "gpt-4o"
        print("   ✅ OpenAI Call Verified")

    # Test Anthropic Dispatch
    print("\n3. Testing Anthropic Dispatch...")
    mock_kb.ai_provider = "anthropic"
    mock_kb.ai_model = "claude-3-opus"
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'content': [{'text': 'Anthropic Response'}]
        }
        mock_post.return_value = mock_response
        
        reply = AIService.generate_smart_reply("Hello", mock_client, mock_kb)
        print(f"   Result: {reply}")
        
        # Verify Call
        args, kwargs = mock_post.call_args
        assert "api.anthropic.com" in args[0]
        assert kwargs['headers']['x-api-key'] == "sk-test-key"
        # Anthropic uses "system" in top level, not messages
        assert kwargs['json']['system'] is not None 
        print("   ✅ Anthropic Call Verified")

if __name__ == "__main__":
    try:
        test_ai_service_dispatch()
        print("\n🎉 All Verification Tests Passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
