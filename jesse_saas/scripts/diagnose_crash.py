import sys
import os
import traceback

from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path)

from app import create_app
from app.models import Client
from app.services.ai_service import AIService

def diagnose():
    app = create_app()
    with app.app_context():
        print("🔍 Starting Diagnosis...")
        
        # 1. Fetch First Client
        client = Client.query.first()
        if not client:
            print("❌ No clients found in DB. Cannot test.")
            return

        print(f"👤 Testing with Client: {client.restaurant_name} (ID: {client.id})")
        
        kb = client.knowledge_base
        if not kb:
            print("❌ Client has no KnowledgeBase!")
            return
            
        print(f"🧠 KnowledgeBase Found (Provider: {kb.ai_provider})")
        
        # 2. Test AI Generation
        print("🚀 Attempting valid request...")
        try:
            reply = AIService.generate_smart_reply("Hello Check", client, kb)
            print(f"✅ Success! Reply: {reply}")
        except Exception:
            print("❌ CRASH DETECTED!")
            traceback.print_exc()

if __name__ == "__main__":
    diagnose()
