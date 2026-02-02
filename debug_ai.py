import sys
import os
import json

# Add project root to path
project_root = r"c:\JESSE.01\jesse_saas"
sys.path.append(project_root)

from app import create_app
from app.models import Client, KnowledgeBase
from app.services.ai_service import AIService

app = create_app()

with app.app_context():
    client = Client.query.first()
    if not client:
        print("No client found")
        sys.exit(1)
    
    kb = client.knowledge_base
    print(f"Testing for Client: {client.restaurant_name}")
    print(f"Operating Hours: {client.operating_hours}")
    print(f"Holiday Dates: {kb.holiday_dates}")
    
    try:
        reply = AIService.generate_smart_reply("Hello", client, kb)
        print("Success! Reply generated.")
    except Exception as e:
        print(f"CRASH DETECTED: {e}")
        import traceback
        traceback.print_exc()
