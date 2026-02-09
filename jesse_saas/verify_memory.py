from app import create_app
from app.services.ai_service import AIService
from app.models import ChatMessage
from app.extensions import db
import time
import uuid

app = create_app()

with app.app_context():
    # Setup
    session_id = f"test_mem_{uuid.uuid4().hex[:8]}"
    client_id = 1
    
    # Mock Objects
    class MockClient:
        id = client_id
        restaurant_name = "Memory Resto"
        plan_type = "pro"
        public_phone = "123"
        def __getitem__(self, item): return getattr(self, item, None)
        def get(self, item, default=None): return getattr(self, item, default)

    class MockKB:
        ai_provider = "openai"
        ai_api_key = "fake" 
        def __getitem__(self, item): return getattr(self, item, None)
        def get(self, item, default=None): return getattr(self, item, default)

    client = MockClient()
    kb = MockKB()

    print(f"\n--- TEST SESSION: {session_id} ---")

    # TEST 1: First Interaction (Say Hello)
    # We expect this to be saved to DB
    print("\n1. Sending: 'Hello, my name is Budi.'")
    # Mocking Call to avoid real API cost, but we need meaningful return
    # Since we can't easily mock inner static methods without patch, we rely on the fact 
    # that verify_reflex or fallback logic might trigger if key is invalid, or it just errors.
    # Let's use the Fallback/Reflex to test memory writing if possible, 
    # OR better: Assume the keys might be valid or we catch error but check DB.
    
    try:
        # We will patch _call_openai to return a fixed string to test memory logic specifically
        from unittest.mock import patch
        
        with patch('app.services.ai_service.AIService._call_openai', return_value="Hello Budi! Nice to meet you.") as mock_llm:
            resp1 = AIService.generate_smart_reply("Hello, my name is Budi.", client, kb, session_id=session_id)
            print(f"AI: {resp1}")
    except Exception as e:
        print(f"Error T1: {e}")

    # TEST 2: Check Database
    print("\n2. Checking DB for Saved Context...")
    msgs = ChatMessage.query.filter_by(session_id=session_id).all()
    print(f"Found {len(msgs)} messages in DB.")
    for m in msgs:
        print(f"[{m.sender}]: {m.content}")

    if len(msgs) >= 2:
        print("SUCCESS: Conversation saved to DB.")
    else:
        print("FAILURE: Database save failed.")

    # TEST 3: Follow-up (Memory Recall)
    # We send a new request with SAME session_id. AI should see previous chat in 'history'.
    print("\n3. Sending Follow-up: 'What is my name?'")
    
    def validation_side_effect(key, model, system, user, temp, tokens, history):
        # We check if 'history' contains Budi
        print(f"DEBUG: Internal History received by LLM: {history}")
        is_mem_present = any("Budi" in m['content'] for m in history)
        if is_mem_present:
            return "Your name is Budi."
        else:
            return "I don't know your name."

    with patch('app.services.ai_service.AIService._call_openai', side_effect=validation_side_effect) as mock_llm:
        resp2 = AIService.generate_smart_reply("What is my name?", client, kb, session_id=session_id)
        print(f"AI: {resp2}")
        
        if "Budi" in resp2:
            print("SUCCESS: AI remembered name from DB history.")
        else:
            print("FAILURE: AI suffered amnesia.")
