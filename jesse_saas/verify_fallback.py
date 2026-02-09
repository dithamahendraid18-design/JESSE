from app import create_app
from app.services.ai_service import AIService
from unittest.mock import patch, MagicMock
import json

app = create_app()

with app.app_context():
    # Mock Models
    class MockClient:
        restaurant_name = "Test Resto"
        operating_hours = None
        timezone = "UTC"
        currency_code = "USD"
        public_phone = "123"
        whatsapp_url = "https://wa.me/123"
        booking_url = "https://book.com"
        website_url = "https://test.com"
        
        def __getitem__(self, item): return getattr(self, item, None)
        def get(self, item, default=None): return getattr(self, item, default)

    class MockKB:
        ai_provider = "openai" # Intentionally set to a specific provider
        ai_api_key = "fake-key"
        
        def __getitem__(self, item): return getattr(self, item, None)
        def get(self, item, default=None): return getattr(self, item, default)

    client = MockClient()
    kb = MockKB()

    print("--- TEST 1: All Providers Fail (Offline Mode) ---")
    # Patch all provider calls to raise Exception
    with patch('app.services.ai_service.AIService._call_openai', side_effect=Exception("OpenAI Down")), \
         patch('app.services.ai_service.AIService._call_anthropic', side_effect=Exception("Anthropic Down")), \
         patch('app.services.ai_service.AIService._call_groq', side_effect=Exception("Groq Down")), \
         patch('app.services.ai_service.AIService._call_openai_compatible', side_effect=Exception("Generic Down")):
        
        response = AIService.generate_smart_reply("Hello", client, kb)
        
        with open("fallback_result.txt", "w", encoding="utf-8") as f:
            f.write(f"Response 1: {response}\n")
        
        if "Connection Issue" in response and "[BUTTON:View Full Menu|open_menu]" in response:
            with open("fallback_result.txt", "a", encoding="utf-8") as f:
                f.write("SUCCESS: Offline Mode Triggered Correctly.\n")

    print("\n--- TEST 2: Primary Fails, Secondary Succeeds ---")
    
    with patch.dict('os.environ', {'GROQ_API_KEY': 'fake-groq-key'}), \
         patch('app.services.ai_service.AIService._call_openai', side_effect=Exception("OpenAI Down")), \
         patch('app.services.ai_service.AIService._call_groq', return_value="Groq Response"):
        
        response = AIService.generate_smart_reply("Hello", client, kb)
        with open("fallback_result.txt", "a", encoding="utf-8") as f:
            f.write(f"Response 2: {response}\n")
        
        if response == "Groq Response":
            with open("fallback_result.txt", "a", encoding="utf-8") as f:
                f.write("SUCCESS: Fallback to Groq worked.\n")
