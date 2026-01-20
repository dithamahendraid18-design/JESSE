import sys
import os
from flask import render_template_string

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'jesse_saas'))

from jesse_saas.app import create_app
from jesse_saas.app.models import Client, MenuItem

app = create_app()

with app.app_context():
    print("Testing DB Access...")
    try:
        client = Client.query.first()
        if not client:
            print("No client found.")
            sys.exit(0)
            
        print(f"Client: {client.name}")
        
        print("Testing MenuItem Query...")
        items = MenuItem.query.filter_by(client_id=client.id).all()
        print(f"Items found: {len(items)}")
        
        print("Testing to_dict() serialization...")
        for item in items:
            d = item.to_dict()
            # print(d) # No print to save space, just accessing
            
        print("Testing Template Rendering (Partial)...")
        # Simulating the variable access in the template
        tmpl = """
        Price: {{ client.currency_code or 'IDR' }}
        Symbol: {{ client.currency_symbol or 'Rp' }}
        {% for item in items %}
            Item: {{ item.name }} - {{ item.price }} - {{ item.allergy_info }}
            JSON: {{ item.to_dict() | tojson }}
        {% endfor %}
        """
        result = render_template_string(tmpl, client=client, items=items)
        print("Template Render Success.")
        
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
