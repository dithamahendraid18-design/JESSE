from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.models import KnowledgeBase
from app.services.upload_service import UploadService

class BotService:
    @staticmethod
    def get_or_create_kb(client_id):
        kb = KnowledgeBase.query.filter_by(client_id=client_id).first()
        if not kb:
            kb = KnowledgeBase(client_id=client_id)
            db.session.add(kb)
            db.session.commit()
        return kb

    @staticmethod
    def update_knowledge_base(client, form_data, files):
        """
        Updates the KnowledgeBase for a client based on form data and file uploads.
        """
        kb = BotService.get_or_create_kb(client.id)

        # 1. Simple Text Fields
        if 'welcome_message' in form_data:
            kb.welcome_message = form_data.get('welcome_message', '').strip()
        
        if 'fallback_message' in form_data:
            kb.fallback_message = form_data.get('fallback_message')

        # 2. JSON Configurations
        starters_json = form_data.get('conversation_starters_json')
        if starters_json:
            kb.conversation_starters = starters_json
            
        menu_flow_json = form_data.get('flow_menu_json')
        if menu_flow_json:
            kb.flow_menu = menu_flow_json

        # 3. Image Handling (Welcome Image)
        # Check for deletion flag
        if form_data.get('delete_welcome_image') == 'true':
            kb.welcome_image_url = None
            
        # Check for new upload
        if 'welcome_image' in files:
            file = files['welcome_image']
            url = UploadService.upload(file, folder='welcome', public_id_prefix=client.public_id)
            if url:
                kb.welcome_image_url = url

        # 4. Book Assets (Cover & Logo)
        
        # Check for deletion flag for Book Cover
        if form_data.get('delete_book_cover') == 'true':
            kb.book_cover_image = None

        # Check for book cover style
        if 'book_cover_style' in form_data:
            kb.book_cover_style = form_data.get('book_cover_style')
            
        # Book Cover Upload
        if 'book_cover' in files:
            file = files['book_cover']
            url = UploadService.upload(file, folder='menu', public_id_prefix=f"cover_{client.public_id}")
            if url:
                kb.book_cover_image = url
                
        # Book Logo
        if 'book_logo' in files:
            file = files['book_logo']
            url = UploadService.upload(file, folder='menu', public_id_prefix=f"logo_{client.public_id}")
            if url:
                kb.book_logo_image = url
                
        # 5. Last Page Content
        if 'last_page_title' in form_data:
            kb.last_page_title = form_data.get('last_page_title')
        if 'last_page_order_desc' in form_data:
            kb.last_page_order_desc = form_data.get('last_page_order_desc')
        if 'last_page_res_desc' in form_data:
            kb.last_page_res_desc = form_data.get('last_page_res_desc')
            
        # 6. Table of Contents
        if 'toc_title' in form_data:
            kb.toc_title = form_data.get('toc_title')
        if 'toc_footer_text' in form_data:
            kb.toc_footer_text = form_data.get('toc_footer_text')

        db.session.commit()
        return kb

    @staticmethod
    def update_ai_settings(client, form_data):
        kb = BotService.get_or_create_kb(client.id)
        
        kb.ai_provider = form_data.get('ai_provider')
        kb.ai_model = form_data.get('ai_model')
        kb.system_prompt = form_data.get('system_prompt')
        
        try:
            kb.temperature = float(form_data.get('temperature', 0.7))
        except ValueError:
            kb.temperature = 0.7
            
        try:
            kb.max_tokens = int(form_data.get('max_tokens', 1024))
        except ValueError:
            kb.max_tokens = 1024
            
        new_key = form_data.get('ai_api_key')
        if new_key and new_key.strip():
            kb.ai_api_key = new_key.strip()
            
        db.session.commit()
        return kb

    @staticmethod
    def update_compliance_settings(client, form_data):
        kb = BotService.get_or_create_kb(client.id)
        
        client.timezone = form_data.get('timezone')
        client.privacy_policy_url = form_data.get('privacy_policy_url')
        client.operating_hours = form_data.get('operating_hours')
        kb.human_handoff_triggers = form_data.get('human_handoff_triggers')
        
        db.session.commit()
        return kb
