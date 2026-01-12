from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app, jsonify
from app.models import Client, KnowledgeBase, InteractionLog, MenuItem
from app.extensions import db
from app.services.analytics import AnalyticsService
from app.services.client_manager import ClientManager
from app.services.upload_service import UploadService
from config import Config
import qrcode
import io
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_logged_in():
    return session.get('admin_logged_in')

@bp.before_request
def require_login():
    if request.endpoint == 'static': # Allow global static files
        return
        
    allowed_routes = ['admin.login', 'admin.static']
    if request.endpoint not in allowed_routes and not is_logged_in():
        return redirect(url_for('admin.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Allow accessing login page even if logged in (to force re-login)
    pass

    if request.method == 'POST':
        password = request.form.get('password')
        admin_pass = Config.ADMIN_PASSWORD
        
        if password == admin_pass:
            session.clear() # Clear old session first
            session['admin_logged_in'] = True
            session.permanent = False # Browser session only (cleared on close)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid Password')
            
    return render_template('admin/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

@bp.route('/dashboard')
def dashboard():
    stats = AnalyticsService.get_dashboard_stats()
    
    # Global Live Feed
    recent_logs = InteractionLog.query.order_by(InteractionLog.timestamp.desc()).limit(15).all()
    
    # Top Performing Assets (Clients by interaction volume)
    # Note: efficient SQL group_by preferred for scale, using list sort for MVP
    all_clients = Client.query.all()
    for c in all_clients:
        c.interaction_count = c.logs.count()
    
    top_clients = sorted(all_clients, key=lambda x: x.interaction_count, reverse=True)[:5]

    return render_template('admin/dashboard.html', 
                           stats=stats,
                           recent_logs=recent_logs,
                           top_clients=top_clients,
                           active_page='dashboard')

@bp.route('/clients')
def clients_list():
    query = request.args.get('q', '').lower()
    status_filter = request.args.get('status', 'all')
    plan_filter = request.args.get('plan', 'all')
    
    clients_query = Client.query
    
    if status_filter != 'all':
        clients_query = clients_query.filter_by(status=status_filter)
    if plan_filter != 'all':
        clients_query = clients_query.filter_by(plan_type=plan_filter)
        
    all_clients = clients_query.all()
    
    # Filter by search string
    if query:
        all_clients = [c for c in all_clients if query in c.restaurant_name.lower() or query in c.public_id.lower()]
    
    stats = AnalyticsService.get_client_stats(status_filter, plan_filter)
    today = datetime.now().date()
    
    return render_template('admin/clients.html', clients=all_clients, active_page='clients', stats=stats, today=today)

@bp.route('/logs')
def system_logs():
    return render_template('admin/logs.html', active_page='logs')

@bp.route('/client/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        name = request.form['restaurant_name']
        plan_type = request.form['plan_type']
        
        new_client = ClientManager.create_client(name, plan_type)
        return redirect(url_for('admin.edit_client', client_id=new_client.id))
        
    return render_template('admin/client_form.html', client=None, kb=None, active_page='clients')

@bp.route('/client/<int:client_id>/edit')
def edit_client(client_id):
    return redirect(url_for('admin.client_hub', client_id=client_id))

@bp.route('/client/<int:client_id>/hub', methods=['GET', 'POST'])
def client_hub(client_id):
    client = Client.query.get_or_404(client_id)
    # Ensure KB exists
    if not client.knowledge_base:
        kb = KnowledgeBase(client_id=client.id)
        db.session.add(kb)
        db.session.commit()
    
    if request.method == 'POST':
        # Delegate to Service
        ClientManager.update_hub_settings(client, request.form, request.files)
        
        # Subscription Dates Handling (Keep simple logic here or move to service if complex)
        sub_start_str = request.form.get('subscription_start')
        if sub_start_str:
            client.subscription_start = datetime.strptime(sub_start_str, '%Y-%m-%d').date()
        else:
            client.subscription_start = None
            
        sub_end_str = request.form.get('subscription_end')
        if sub_end_str:
            client.subscription_end = datetime.strptime(sub_end_str, '%Y-%m-%d').date()
        else:
            client.subscription_end = None
        
        db.session.commit()
        
        flash('Hub settings saved.', 'success')
        return redirect(url_for('admin.client_hub', client_id=client.id))

    return render_template('admin/hub.html', client=client, active_page='hub')

@bp.route('/client/<int:client_id>/menu-book', methods=['GET', 'POST'])
def client_menu_book(client_id):
    client = Client.query.get_or_404(client_id)
    # Ensure KB exists
    if not client.knowledge_base:
        db.session.add(KnowledgeBase(client_id=client.id))
        db.session.commit()
    
    if request.method == 'POST':
        # 1. Update Client Theme Color
        if 'theme_color' in request.form:
            client.theme_color = request.form['theme_color']
            
        # 1.5 Update Book Theme Color (New)
        if 'book_theme_color' in request.form:
            # Only update if it's a valid hex or empty?
            # Assuming form sends hex.
            client.knowledge_base.book_theme_color = request.form['book_theme_color']
        
        # 2. Update Welcome Image (Cover) via BotService logic or direct reuse
        from app.services.bot_service import BotService
        # We can reuse update_knowledge_base but it expects full form data. 
        # Let's do a targeted update here for simplicity or call the service if it's robust enough.
        # Calling service is cleaner if it handles partial updates safely. 
        # Checking BotService.update_knowledge_base... it looks at keys. So it is safe.
        BotService.update_knowledge_base(client, request.form, request.files)

        flash('Digital Book settings saved.', 'success')
        return redirect(url_for('admin.client_menu_book', client_id=client.id))
        
    return render_template('admin/menu_book.html', client=client, active_page='menu_book')

@bp.route('/client/<int:client_id>/menu', methods=['GET', 'POST'])
def client_menu(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        category = request.form['category']
        description = request.form.get('description')
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            image_url = UploadService.upload(file, folder='menu', public_id_prefix=f"{client.public_id}")
        
        item = MenuItem(
            client_id=client.id,
            name=name,
            price=price,
            category=category,
            description=description,
            image_url=image_url,
            is_available=True
        )
        db.session.add(item)
        db.session.commit()
        flash('Menu item added.', 'success')
        return redirect(url_for('admin.client_menu', client_id=client.id))

    menu_items = client.menu_items.order_by(MenuItem.category.desc(), MenuItem.name).all()
    return render_template('admin/menu.html', client=client, menu_items=menu_items, active_page='menu')

@bp.route('/client/<int:client_id>/menu/<int:item_id>/edit', methods=['POST'])
def client_menu_edit(client_id, item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.client_id != client_id:
        return "Unauthorized", 403
        
    item.name = request.form['name']
    item.price = float(request.form['price'])
    item.category = request.form['category']
    item.description = request.form.get('description')
    
    if 'image' in request.files:
        file = request.files['image']
        url = UploadService.upload(file, folder='menu', public_id_prefix=f"{item.client.public_id}")
        if url:
             item.image_url = url

    db.session.commit()
    flash('Item updated.', 'success')
    return redirect(url_for('admin.client_menu', client_id=client_id))

@bp.route('/client/<int:client_id>/menu/<int:item_id>/toggle', methods=['POST'])
def client_menu_toggle(client_id, item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.client_id != client_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    item.is_available = not item.is_available
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'new_status': item.is_available,
        'item_id': item.id
    })

@bp.route('/client/<int:client_id>/menu/<int:item_id>/delete', methods=['POST'])
def client_menu_delete(client_id, item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.client_id != client_id:
        return "Unauthorized", 403
    
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('admin.client_menu', client_id=client_id))

@bp.route('/client/<int:client_id>/bot-builder', methods=['GET', 'POST'])
def client_bot(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        from app.services.bot_service import BotService
        BotService.update_knowledge_base(client, request.form, request.files)
        flash('Bot settings saved.', 'success')
        return redirect(url_for('admin.client_bot', client_id=client.id))

    kb = client.knowledge_base
    if not kb:
        kb = KnowledgeBase(client_id=client.id)
        db.session.add(kb)
        db.session.commit()

    # Parse starters for template
    starters_list = []
    if kb.conversation_starters:
        try:
            starters_list = json.loads(kb.conversation_starters)
        except:
            starters_list = []

    return render_template('admin/bot_builder.html', client=client, kb=kb, starters_list=starters_list, active_page='bot')

@bp.route('/client/<int:client_id>/ai-settings', methods=['GET', 'POST'])
def client_ai(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        from app.services.bot_service import BotService
        BotService.update_ai_settings(client, request.form)
        flash('AI Settings updated successfully.', 'success')
        return redirect(url_for('admin.client_ai', client_id=client.id))

    kb = client.knowledge_base
    if not kb:
        kb = KnowledgeBase(client_id=client.id)
        db.session.add(kb)
        db.session.commit()

    return render_template('admin/ai_settings.html', client=client, kb=kb, active_page='ai_settings')

@bp.route('/client/<int:client_id>/compliance', methods=['GET', 'POST'])
def client_compliance(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        from app.services.bot_service import BotService
        BotService.update_compliance_settings(client, request.form)
        flash('Compliance settings updated.', 'success')
        return redirect(url_for('admin.client_compliance', client_id=client.id))

    kb = client.knowledge_base
    if not kb:
        kb = KnowledgeBase(client_id=client.id)
        db.session.add(kb)
        db.session.commit()

    return render_template('admin/compliance.html', client=client, kb=kb, active_page='compliance')

@bp.route('/client/<int:client_id>/publish', methods=['GET', 'POST'])
def client_publish(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.is_maintenance_mode = True if request.form.get('is_maintenance_mode') == 'true' else False
        client.allowed_domains = request.form.get('allowed_domains')
        db.session.commit()
        flash('Publish settings updated.', 'success')
        return redirect(url_for('admin.client_publish', client_id=client.id))

    return render_template('admin/publish.html', client=client, active_page='publish')

@bp.route('/client/<int:client_id>/qr')
def client_qr(client_id):
    client = Client.query.get_or_404(client_id)
    target_url = f"{request.host_url}chat/{client.public_id}"
    
    # Use SVG factory to avoid Pillow dependency (saves ~50MB)
    import qrcode.image.svg
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(target_url, image_factory=factory)
    
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return send_file(buf, mimetype='image/svg+xml')

@bp.route('/client/<int:client_id>/stats')
@bp.route('/client/<int:client_id>/stats/<view_mode>')
def client_stats(client_id, view_mode='overview'):
    client = Client.query.get_or_404(client_id)
    
    if view_mode not in ['overview', 'conversations', 'events', 'trends', 'reports']:
        view_mode = 'overview'
    
    context = {}
    
    if view_mode == 'overview':
        context['total_conversations'] = client.logs.count()
        context['total_clients'] = 1 
        total = client.logs.count()
        ai_chats = client.logs.filter_by(interaction_type='ai_chat').count()
        context['ai_ratio'] = round((ai_chats / total * 100), 1) if total > 0 else 0
    
    elif view_mode == 'conversations':
        context['logs'] = client.logs.order_by(InteractionLog.timestamp.desc()).limit(50).all()

    elif view_mode == 'events':
        context['events_breakdown'] = {
            'Menu Clicks': client.logs.filter(InteractionLog.interaction_type == 'button_click', InteractionLog.user_query.ilike('%menu%')).count(),
            'Location Clicks': client.logs.filter(InteractionLog.interaction_type == 'button_click', InteractionLog.user_query.ilike('%location%')).count(),
            'Contact Clicks': client.logs.filter(InteractionLog.interaction_type == 'button_click', InteractionLog.user_query.ilike('%contact%')).count()
        }

    return render_template('admin/analytics.html', client=client, view_mode=view_mode, active_page=view_mode, **context)

@bp.route('/upload/bot-image', methods=['POST'])
@bp.route('/upload/bot-image', methods=['POST'])
def upload_bot_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            filename = secure_filename(f"bot_{datetime.now().timestamp()}_{file.filename}")
            # Use UPLOAD_FOLDER from config + 'bot_images'
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'bot_images')
            
            # Ensure upload folder exists (crucial for local/tmp)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save File
            # Save File via Service
            url = UploadService.upload(file, folder='bot_images')
            
            if not url:
                return jsonify({'error': 'Upload failed'}), 500
                
            # If local return, we need to wrap it in url_for, but UploadService returns path relative to upload folder?
            # Our UploadService returns either http URL OR "folder/filename".
            
            if UploadService.is_remote_url(url):
                return jsonify({'url': url})
            else:
                # Local fallback logic
                return jsonify({'url': url_for('uploaded_file', filename=url)})
            
    except Exception as e:
        print(f"UPLOAD ERROR: {str(e)}") # Log to Vercel/Console
        return jsonify({'error': f"Server Error: {str(e)}"}), 500

    return jsonify({'error': 'Upload failed unknown'}), 500
