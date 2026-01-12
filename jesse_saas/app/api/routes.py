from flask import Blueprint, request, jsonify
from app.models import Client, KnowledgeBase, InteractionLog
from app.extensions import db
from app.services.upload_service import UploadService

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/config/<public_id>', methods=['GET'])
def get_client_config(public_id):
    client = Client.query.filter_by(public_id=public_id).first()
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    import json
    kb = client.knowledge_base
    starters = []
    if kb and kb.conversation_starters:
        try:
            starters = json.loads(kb.conversation_starters)
        except:
            starters = []

    
    def resolve_url(path, folder):
        if not path: return None
        if UploadService.is_remote_url(path): return path
        # If local logic (folder/filename)
        if '/' in path:
            return request.host_url + 'static/uploads/' + path
        # Legacy local logic (filename only)
        return request.host_url + f'static/uploads/{folder}/' + path

    return jsonify({
        "restaurant_name": client.restaurant_name,
        "theme_color": client.theme_color,
        "plan_type": client.plan_type,
        "welcome_message": kb.welcome_message if kb else "Welcome!",
        "avatar_url": resolve_url(kb.avatar_image, 'avatars') if kb else None,
        "welcome_image_url": resolve_url(kb.welcome_image_url, 'welcome') if kb else None,
        "conversation_starters": starters
    }), 200

@bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    public_id = data.get('public_id')
    message_type = data.get('type') # 'button_click' or 'text_input'
    message_content = data.get('message')

    if not public_id:
        return jsonify({"error": "Missing public_id"}), 400

    # Step 1: Identification
    client = Client.query.filter_by(public_id=public_id).first()
    if not client:
        return jsonify({"error": "Client not found"}), 404

    # Step 2: Tier Validation (Strict)
    if message_type == 'text_input' and client.plan_type == 'basic':
        return jsonify({
            "error": "Unauthorized", 
            "message": "Text chat is a Pro feature."
        }), 403

    response_data = {}

    # Step 3: Handle Button Clicks (Free Tier)
    if message_type == 'button_click':
        kb = client.knowledge_base
        if not kb:
            # If no KB exists, handle gracefully
            return jsonify({"response": "No knowledge base configured."}), 200

        msg_lower = (message_content or "").lower()
        
        reply = "I don't have that information."
        
        if "menu" in msg_lower:
            text = kb.flow_menu or "Here is our menu:"
            menu_url = kb.menu_url if kb.menu_url else None
            # If menu_url is stored but it's a file? Current logic: menu_url is a String URL usually.
            # But what if I want to serve the digital menu book URL?
            # Standard logic: menu_url text field.
            
            reply = f"{text}\n\n[Open Menu]({menu_url})" if menu_url else (text if kb.flow_menu else "Menu not available.")
        
        elif "wifi" in msg_lower:
            reply = f"WiFi Password: {kb.wifi_password}" if kb.wifi_password else "No WiFi information."
        
        elif "hours" in msg_lower:
            reply = kb.flow_hours or (f"Our hours are: {kb.opening_hours}" if kb.opening_hours else "Hours not specified.")
        
        elif "location" in msg_lower:
            reply = kb.flow_location or (f"We are located at: {kb.location_address}" if kb.location_address else "Address not specified.")
        
        elif "about" in msg_lower:
            reply = kb.flow_about or (kb.about_us if kb.about_us else "I don't have information about us yet.")
        
        elif "reservation" in msg_lower or "contact" in msg_lower:
            text = kb.flow_contact or "Contact us or book a table:"
            reply = f"{text}\n\n[Book Now]({kb.reservation_url})" if kb.reservation_url else (text if kb.flow_contact else "Reservations not configured.")
        
        response_data = {"response": reply}

        # Log Interaction
        log = InteractionLog(
            client_id=client.id,
            interaction_type='button_click',
            user_query=message_content
        )
        db.session.add(log)
        db.session.commit()

    # Step 4: Handle Text Input (Pro Tier)
    elif message_type == 'text_input':
        # Real AI Response
        from app.services.ai_service import generate_smart_reply
        kb = client.knowledge_base
        
        # Pass both client object and KB object
        ai_reply = generate_smart_reply(message_content, client, kb)
        response_data = {"response": ai_reply}
        
        # Log Interaction
        log = InteractionLog(
            client_id=client.id,
            interaction_type='ai_chat',
            user_query=message_content
        )
        db.session.add(log)
        db.session.commit()

    return jsonify(response_data), 200
