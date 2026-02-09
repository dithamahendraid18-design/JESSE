from app import create_app
from app.services.vector_service import VectorService
import os

app = create_app()

with app.app_context():
    # TEST 1: Simulate HF Failure (Remove Key)
    print("\n--- TEST 1: SQL Fallback (No API Key) ---")
    original_key = os.environ.get('HUGGINGFACE_API_KEY')
    if original_key: del os.environ['HUGGINGFACE_API_KEY']
    
    try:
        # Assuming Client ID 1 exists and has menu items like "Burger" or "Pasta" or "Tea"
        # We try a query that should match a keyword
        query = "Show me the Burger"
        results = VectorService.search_menu(1, query)
        
        print(f"Query: {query}")
        print(f"Results Found: {len(results)}")
        for item in results:
            print(f"- {item.name}: {item.description}")
            
        if len(results) > 0:
            print("SUCCESS: Items returned via SQL Fallback.")
        else:
            print("WARNING: No items found. Ensure 'Burger' is in DB for Client 1.")

    except Exception as e:
        print(f"FAILURE: {e}")
    finally:
        # Restore key
        if original_key: os.environ['HUGGINGFACE_API_KEY'] = original_key
