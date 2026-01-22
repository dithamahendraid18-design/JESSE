import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_service import AIService

class DummyObj:
    def __getattr__(self, name):
        return None

def test_menu_injection():
    print("🍔 Testing Menu Data Injection...")
    
    # 1. Mock Client & KB
    mock_client = DummyObj()
    mock_client.id = 999
    mock_client.restaurant_name = "Burger Kingdom"
    mock_client.public_phone = "555-1234"
    mock_client.maps_url = "http://maps.google.com/burger"
    mock_client.delivery_partners = '[{"platform": "Uber", "url": "http://uber.com/burger"}]'
    mock_client.wifi_ssid = "BurgerFreeWiFi"
    mock_client.wifi_password = "burgerpass123"
    mock_client.review_url = "http://review.me/burger"
    mock_client.booking_url = "http://book.me/burger"
    mock_client.currency_code = "USD"
    mock_client.currency_symbol = "$"
    # Existing fields needed for context
    mock_client.public_email = "info@burger.com"
    mock_client.instagram_url = "http://inst.com/burger"
    mock_client.website_url = "http://burger.com"
    mock_client.delivery_url = "http://deliver.com"

    
    mock_kb = DummyObj()
    mock_kb.ai_provider = 'mock' # Mock provider to avoid actual API call if possible, or we mock the request
    mock_kb.ai_api_key = 'test'
    
    # 2. Mock Menu Items
    mock_items = []
    item1 = DummyObj()
    item1.name = "Big Mac"
    item1.price = 5.99
    item1.description = "Two all-beef patties."
    mock_items.append(item1)
    
    item2 = DummyObj()
    item2.name = "Fries"
    item2.price = 2.99
    item2.description = None
    mock_items.append(item2)

    # 3. Patch the DB Query and Request
    with patch('app.models.MenuItem.query') as mock_query:
        # returns query object, then filter_by returns query object, then all() returns list
        mock_filter = MagicMock()
        mock_filter.all.return_value = mock_items
        
        mock_query_obj = MagicMock()
        mock_query_obj.filter_by.return_value = mock_filter
        
        mock_query.filter_by = MagicMock(return_value=mock_filter) # Patch filter_by directly? 
        # Actually in the code: MenuItem.query.filter_by(...).all()
        # So MenuItem.query is the property.
        
        # Let's use a simpler patch if possible, or just mock the AIService internal method?
        # No, we want to test the `generate_smart_reply` formatting.
        
        # Proper SQLAlchemy Mocking is tricky. 
        # Let's mock `MenuItem` class attribute `query`
        MenuItemMock = MagicMock()
        MenuItemMock.query.filter_by.return_value.all.return_value = mock_items
        
        with patch('app.services.ai_service.MenuItem', MenuItemMock):
            with patch('app.services.ai_service.requests.post') as mock_post:
                # Mock API response
                mock_response = MagicMock()
                mock_response.json.return_value = {'choices': [{'message': {'content': 'OK'}}]}
                mock_post.return_value = mock_response
                
                # EXECUTE
                AIService.generate_smart_reply("Hi", mock_client, mock_kb)
                
                # VERIFY
                args, kwargs = mock_post.call_args
                payload = kwargs['json']
                messages = payload['messages']
                system_msg = messages[0]['content']
                
                print("\n[System Prompt Inspection]")
                print("-" * 40)
                # print(system_msg) 
                # Don't print full prompt to keep logs clean, just check assertions
                
                # Check for Menu Items
                if "Big Mac ($5.99): Two all-beef patties." in system_msg:
                    print("✅ Menu Item 1 Found")
                else:
                    print("❌ Menu Item 1 Missing")
                    
                if "Fries ($2.99)" in system_msg:
                    print("✅ Menu Item 2 Found")
                else:
                    print("❌ Menu Item 2 Missing")
                    
                # Check for Button Instructions
                if "[BUTTON:View Menu|open_menu]" in system_msg:
                    print("✅ Smart Button Instruction Found")
                else:
                    print("❌ Smart Button Instruction Missing")

                # Check Client Hub Data Injection
                checks = {
                    "Phone": "555-1234",
                    "Maps": "http://maps.google.com/burger",
                    "DeliveryPartner": "Uber: http://uber.com/burger",
                    "WiFi SSID": "BurgerFreeWiFi",
                    "WiFi Pass": "burgerpass123",
                    "Review": "http://review.me/burger",
                    "Booking": "http://book.me/burger",
                    "Currency": "USD ($)"
                }
                
                print("\nChecking New Client Hub Fields:")
                for name, value in checks.items():
                    if value in system_msg:
                        print(f"✅ {name} Found")
                    else:
                        print(f"❌ {name} Missing (Expected '{value}')")
                        print(f"   Context snippet: {system_msg[system_msg.find('CONTEXT'):system_msg.find('MENU ITEMS')]}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            test_menu_injection()
        except Exception as e:
            print(f"❌ Error: {e}")
