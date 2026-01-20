import uuid
from datetime import datetime
from .extensions import db

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    restaurant_name = db.Column(db.String(100), nullable=False)
    
    # Plan: 'basic' or 'pro'
    plan_type = db.Column(db.String(20), default='basic')
    
    # Status: 'active', 'inactive'
    status = db.Column(db.String(20), default='active')
    
    # Widget Styling
    theme_color = db.Column(db.String(7), default='#000000')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin Note (Phase 25)
    billing_note = db.Column(db.Text, nullable=True)

    # SEO & Subscription (Phase 26)
    slug = db.Column(db.String(100), unique=True, nullable=True)
    renewal_date = db.Column(db.Date, nullable=True) # Kept for backward compatibility or simple view
    subscription_start = db.Column(db.Date, nullable=True)
    subscription_end = db.Column(db.Date, nullable=True)

    # Phase 27: Admin Studio Control
    is_maintenance_mode = db.Column(db.Boolean, default=False)
    allowed_domains = db.Column(db.Text, nullable=True) # JSON or comma-separated
    
    # Phase 28: Compliance & Operations
    operating_hours = db.Column(db.Text, nullable=True) # JSON structure
    timezone = db.Column(db.String(50), default='UTC')
    privacy_policy_url = db.Column(db.String(255), nullable=True)

    # Phase 29: Regional & Socials (Global Pivot)
    language = db.Column(db.String(50), default='English (US)')
    currency_code = db.Column(db.String(10), default='USD')
    currency_symbol = db.Column(db.String(5), default='$')
    
    owner_phone = db.Column(db.String(20), nullable=True) # Admin Internal
    owner_email = db.Column(db.String(100), nullable=True) # Admin Internal
    public_phone = db.Column(db.String(20), nullable=True) # Public Reservation
    public_email = db.Column(db.String(100), nullable=True) # Public Enquiry
    
    address = db.Column(db.Text, nullable=True)
    maps_url = db.Column(db.String(255), nullable=True)
    delivery_url = db.Column(db.String(255), nullable=True) # Deprecated by delivery_partners
    delivery_partners = db.Column(db.Text, nullable=True) # JSON structure: [{platform, url}]
    instagram_url = db.Column(db.String(255), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)

    # Phase 30: Branding & Billing (International Upgrade)
    widget_position = db.Column(db.String(20), default='right') # right/left
    is_white_labeled = db.Column(db.Boolean, default=False)
    price_includes_tax = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(50), nullable=True) # Admin record

    # Phase 31: Guest Experience (WiFi & Reviews)
    wifi_ssid = db.Column(db.String(100), nullable=True)
    wifi_password = db.Column(db.String(100), nullable=True)
    review_url = db.Column(db.String(255), nullable=True)
    booking_url = db.Column(db.String(255), nullable=True)

    # Relationships
    knowledge_base = db.relationship('KnowledgeBase', backref='client', uselist=False, cascade="all, delete-orphan")
    menu_items = db.relationship('MenuItem', backref='client', lazy='dynamic', cascade="all, delete-orphan")
    logs = db.relationship('InteractionLog', backref='client', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.restaurant_name} ({self.plan_type})>"


class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, unique=True)
    
    about_us = db.Column(db.Text, nullable=True)
    menu_url = db.Column(db.String(255), nullable=True)
    reservation_url = db.Column(db.String(255), nullable=True)
    location_address = db.Column(db.String(255), nullable=True)
    opening_hours = db.Column(db.Text, nullable=True)
    wifi_password = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    welcome_message = db.Column(db.Text, default="Welcome! How can I help you?")
    welcome_image_url = db.Column(db.String(255), nullable=True) # Hero Image
    avatar_image = db.Column(db.String(255), nullable=True)
    menu_image = db.Column(db.String(255), nullable=True)
    
    # Custom Book Styling
    book_theme_color = db.Column(db.String(7), nullable=True) # e.g. #8B4513
    book_cover_image = db.Column(db.String(255), nullable=True) # Specific Portrait Cover
    book_cover_style = db.Column(db.String(20), default='cover') # 'cover' or 'contain'
    category_order = db.Column(db.Text, nullable=True) # JSON list of ordered categories: ["Food", "Drink", "Dessert"]
    book_logo_image = db.Column(db.String(255), nullable=True) # Logo on cover
    
    # Last Page / Back Cover Content
    last_page_title = db.Column(db.String(100), default="Thank You for Visiting")
    last_page_order_desc = db.Column(db.Text, default="Enjoy our food from the comfort of your home. We deliver straight to your door.")
    last_page_res_desc = db.Column(db.Text, default="Planning a special dinner? Book a table with us and let us serve you.")

    # Table of Contents Content
    toc_title = db.Column(db.String(100), default="Table of Contents")
    toc_footer_text = db.Column(db.String(200), default="Tap to browse menu")
    
    # Dynamic Intent Flows
    flow_menu = db.Column(db.Text, nullable=True)
    flow_hours = db.Column(db.Text, nullable=True)
    flow_location = db.Column(db.Text, nullable=True)
    flow_about = db.Column(db.Text, nullable=True)
    flow_contact = db.Column(db.Text, nullable=True)

    # Extended Details (Phase 19)
    payment_methods = db.Column(db.Text, nullable=True)
    parking_info = db.Column(db.Text, nullable=True)
    dietary_info = db.Column(db.Text, nullable=True)
    policy_info = db.Column(db.Text, nullable=True)

    # Phase 27: AI Persona Config
    system_prompt = db.Column(db.Text, nullable=True)
    
    # AI Engine Config
    ai_provider = db.Column(db.String(50), default='groq') # groq, openai, anthropic
    ai_model = db.Column(db.String(100), default='llama3-70b-8192')
    ai_api_key = db.Column(db.String(255), nullable=True)
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=1024)

    # Legacy/Fallback
    fallback_message = db.Column(db.Text, nullable=True)
    conversation_starters = db.Column(db.Text, nullable=True) # JSON string
    human_handoff_triggers = db.Column(db.Text, nullable=True) # Comma-separated

    def __repr__(self):
        return f"<KnowledgeBase for Client {self.client_id}>"


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True) # Food, Drink, Dessert
    price = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255), nullable=True)
    allergy_info = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'description': self.description,
            'image_url': self.image_url,
            'allergy_info': self.allergy_info,
            'is_available': self.is_available
        }

    def __repr__(self):
        return f"<MenuItem {self.name} - {self.client_id}>"



class InteractionLog(db.Model):
    __tablename__ = 'interaction_logs'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # 'button_click' or 'ai_chat'
    interaction_type = db.Column(db.String(50), nullable=False)
    
    user_query = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Log {self.interaction_type} - {self.timestamp}>"
