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
        client.plan_type = form_data.get('plan_type')
        client.billing_note = form_data.get('billing_note')
        
        # Branding & Billing
        client.font_style = form_data.get('font_style')
        client.widget_position = form_data.get('widget_position')
        client.is_white_labeled = form_data.get('is_white_labeled') == 'on'
        client.price_includes_tax = form_data.get('price_includes_tax') == 'on'
        client.payment_method = form_data.get('payment_method')
        
        # Guest Experience
        client.wifi_ssid = form_data.get('wifi_ssid')
        client.wifi_password = form_data.get('wifi_password')
        client.review_url = form_data.get('review_url')
        client.booking_url = form_data.get('booking_url')
        client.deposit_policy = form_data.get('deposit_policy')
        client.late_arrival_policy = form_data.get('late_arrival_policy')
        
        # Facilities & Capacity
        client.total_seating = form_data.get('total_seating')
        client.max_group_size = form_data.get('max_group_size')
        client.seating_configuration = form_data.get('seating_configuration')
        client.has_private_room = form_data.get('has_private_room') == 'on'
        client.private_room_capacity = form_data.get('private_room_capacity')
        client.facilities_list = form_data.get('facilities_list')
        client.family_facilities_list = form_data.get('family_facilities_list')
        
        # Regional & Contact
        client.language = form_data.get('language')
        client.currency_code = form_data.get('currency_code')
        
        symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': '$', 'IDR': 'Rp'}
        client.currency_symbol = symbols.get(client.currency_code, '$')
        
        client.owner_phone = form_data.get('owner_phone')
        client.owner_email = form_data.get('owner_email')
        client.operating_hours = form_data.get('operating_hours')
        client.timezone = form_data.get('timezone')
        client.public_phone = form_data.get('public_phone')
        client.public_email = form_data.get('public_email')
        client.address = form_data.get('address')
        client.maps_url = form_data.get('maps_url')
        client.website_url = form_data.get('website_url')
        client.parking_info = form_data.get('parking_info')
        client.direction_note = form_data.get('direction_note')
        client.delivery_partners = form_data.get('delivery_partners') 
        client.delivery_partners = form_data.get('delivery_partners') 
        client.instagram_url = form_data.get('instagram_url')
        client.tiktok_url = form_data.get('tiktok_url')
        client.youtube_url = form_data.get('youtube_url')
        client.whatsapp_url = form_data.get('whatsapp_url')

        # Avatar Upload
        if files and 'avatar' in files:
            file = files['avatar']
            if file and file.filename != '':
                # Upload via Service
                url = UploadService.upload(file, folder='avatars', public_id_prefix=client.public_id)
                if url:
                    client.knowledge_base.avatar_image = url

        # Knowledge Base Updates (Guest Experience)
        if client.knowledge_base:
            client.knowledge_base.payment_methods = form_data.get('accepted_payment_methods')
            client.knowledge_base.policy_info = form_data.get('house_rules')

        db.session.commit()
        return client
