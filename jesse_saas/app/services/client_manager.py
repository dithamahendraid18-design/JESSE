import re
try:
    from slugify import slugify
except ImportError:
    # Simple fallback
    def slugify(text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        return re.sub(r'[-\s]+', '-', text).strip('-')

from app.models import Client, KnowledgeBase
from app.extensions import db
from app.services.upload_service import UploadService

class ClientManager:
    @staticmethod
    def create_client(restaurant_name, plan_type):
        """
        Create a new client with a unique slug and an empty KnowledgeBase.
        """
        # Generate unique slug
        base_slug = slugify(restaurant_name)
        slug = base_slug
        counter = 1
        
        while Client.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        new_client = Client(
            restaurant_name=restaurant_name,
            plan_type=plan_type,
            slug=slug
        )
        db.session.add(new_client)
        db.session.commit()
        
        # Create Empty KB
        kb = KnowledgeBase(client_id=new_client.id)
        db.session.add(kb)
        db.session.commit()
        
        return new_client

    @staticmethod
    def update_hub_settings(client, form_data, files=None):
        """
        Update client hub settings from form data.
        """
        # Basic Info
        client.restaurant_name = form_data.get('restaurant_name')
        client.slug = form_data.get('slug')
        client.status = form_data.get('status')
        client.theme_color = form_data.get('theme_color')
        client.plan_type = form_data.get('plan_type')
        client.billing_note = form_data.get('billing_note')
        
        # Branding & Billing
        client.widget_position = form_data.get('widget_position')
        client.is_white_labeled = form_data.get('is_white_labeled') == 'on'
        client.price_includes_tax = form_data.get('price_includes_tax') == 'on'
        client.payment_method = form_data.get('payment_method')
        
        # Guest Experience
        client.wifi_ssid = form_data.get('wifi_ssid')
        client.wifi_password = form_data.get('wifi_password')
        client.review_url = form_data.get('review_url')
        client.booking_url = form_data.get('booking_url')
        
        # Regional & Contact
        client.language = form_data.get('language')
        client.currency_code = form_data.get('currency_code')
        
        symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': '$', 'IDR': 'Rp'}
        client.currency_symbol = symbols.get(client.currency_code, '$')
        
        client.owner_phone = form_data.get('owner_phone')
        client.owner_email = form_data.get('owner_email')
        client.timezone = form_data.get('timezone')
        client.public_phone = form_data.get('public_phone')
        client.public_email = form_data.get('public_email')
        client.address = form_data.get('address')
        client.maps_url = form_data.get('maps_url')
        client.website_url = form_data.get('website_url')
        client.delivery_partners = form_data.get('delivery_partners') 
        client.instagram_url = form_data.get('instagram_url')

        # Avatar Upload
        if files and 'avatar' in files:
            file = files['avatar']
            if file and file.filename != '':
                # Upload via Service
                url = UploadService.upload(file, folder='avatars', public_id_prefix=client.public_id)
                if url:
                    client.knowledge_base.avatar_image = url

        db.session.commit()
        return client
