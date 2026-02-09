from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from . import bp
from app.models import Client, KnowledgeBase
from app.services.bot_service import BotService
from app.services.upload_service import UploadService
from app.extensions import db
import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime

@bp.route('/client/<int:client_id>/bot-builder', methods=['GET', 'POST'])
def client_bot(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
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
        BotService.update_compliance_settings(client, request.form)
        flash('Compliance settings updated.', 'success')
        return redirect(url_for('admin.client_compliance', client_id=client.id))

    kb = client.knowledge_base
    if not kb:
        kb = KnowledgeBase(client_id=client.id)
        db.session.add(kb)
        db.session.commit()

    return render_template('admin/compliance.html', client=client, kb=kb, active_page='compliance')

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
            url = UploadService.upload(file, folder='bot_images')
            
            if not url:
                return jsonify({'error': 'Upload failed'}), 500
                
            if UploadService.is_remote_url(url):
                return jsonify({'url': url})
            else:
                # Local fallback logic
                return jsonify({'url': url_for('uploaded_file', filename=url)})
            
    except Exception as e:
        print(f"UPLOAD ERROR: {str(e)}") # Log to Vercel/Console
        return jsonify({'error': f"Server Error: {str(e)}"}), 500

    return jsonify({'error': 'Upload failed unknown'}), 500
