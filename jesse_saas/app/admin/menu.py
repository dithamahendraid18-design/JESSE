from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from . import bp
from app.models import Client, KnowledgeBase, MenuItem
from app.services.menu_service import MenuService
from app.services.bot_service import BotService
from app.extensions import db
import json
import threading

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
            client.knowledge_base.book_theme_color = request.form['book_theme_color']
        
        # 2. Update Welcome Image (Cover) via BotService logic or direct reuse
        BotService.update_knowledge_base(client, request.form, request.files)

        flash('Digital Book settings saved.', 'success')
        return redirect(url_for('admin.client_menu_book', client_id=client.id))
        
    return render_template('admin/menu_book.html', client=client, active_page='menu_book')

@bp.route('/client/<int:client_id>/menu', methods=['GET', 'POST'])
def client_menu(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            MenuService.create_item(client, request.form, request.files)
            flash('Menu item added.', 'success')
        except ValueError as e:
            flash(str(e), 'error')
            
        return redirect(url_for('admin.client_menu', client_id=client.id))

    menu_items = MenuService.get_items(client.id)
    
    # Refactor: Group by Category for Admin View
    menu_by_cat = {}
    for item in menu_items:
        cat = item.category or 'Other'
        if cat not in menu_by_cat:
            menu_by_cat[cat] = []
        menu_by_cat[cat].append(item)

    # Sort Categories
    sorted_categories = []
    if client.knowledge_base and client.knowledge_base.category_order:
        try:
            saved_order = json.loads(client.knowledge_base.category_order)
            for cat in saved_order:
                if cat in menu_by_cat:
                    sorted_categories.append(cat)
        except:
            pass
    
    # Append remaining categories
    remaining = sorted([k for k in menu_by_cat.keys() if k not in sorted_categories])
    sorted_categories.extend(remaining)

    return render_template('admin/menu.html', client=client, 
                         menu_items=menu_items, # Keep raw list just in case (optional, but harmless)
                         menu_by_cat=menu_by_cat,
                         sorted_categories=sorted_categories,
                         active_page='menu')

@bp.route('/client/<int:client_id>/menu/<int:item_id>/edit', methods=['POST'])
def client_menu_edit(client_id, item_id):
    try:
        MenuService.update_item(item_id, request.form, request.files, client_id_check=client_id)
        flash('Item updated.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        
    return redirect(url_for('admin.client_menu', client_id=client.id))

@bp.route('/client/<int:client_id>/menu/<int:item_id>/toggle', methods=['POST'])
def client_menu_toggle(client_id, item_id):
    try:
        new_status = MenuService.toggle_availability(item_id, client_id_check=client_id)
        return jsonify({
            'success': True, 
            'new_status': new_status,
            'item_id': item_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@bp.route('/client/<int:client_id>/menu/<int:item_id>/delete', methods=['POST'])
def client_menu_delete(client_id, item_id):
    try:
        MenuService.delete_item(item_id, client_id_check=client_id)
        flash('Item deleted.')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        
    return redirect(url_for('admin.client_menu', client_id=client.id))

@bp.route('/client/<int:client_id>/menu/reorder-categories', methods=['POST'])
def client_menu_reorder_categories(client_id):
    client = Client.query.get_or_404(client_id)
    kb = client.knowledge_base
    if not kb:
         return jsonify({'error': 'KB not found'}), 404
         
    try:
        data = request.get_json()
        new_order = data.get('order', []) # Expect list of strings
        kb.category_order = json.dumps(new_order)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/client/<int:client_id>/menu/labels', methods=['POST'])
def client_menu_labels(client_id):
    client = Client.query.get_or_404(client_id)
    kb = client.knowledge_base
    if not kb:
         return jsonify({'error': 'KB not found'}), 404
         
    try:
        data = request.get_json()
        kb.label_colors = json.dumps(data)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/maintenance/sync-menu')
def sync_menu_embeddings():
    from .auth import is_logged_in
    if not is_logged_in(): return redirect(url_for('admin.login'))
    
    from app.services.vector_service import VectorService
    
    # Background Worker
    def run_sync(app):
        with app.app_context():
            print("--- [Background] Menu Sync Started ---")
            unsynced = MenuItem.query.filter((MenuItem.embedding_synced == False) | (MenuItem.embedding_synced == None)).all()
            success, fail = 0, 0
            for item in unsynced:
                try:
                    if VectorService.upsert_item_embedding(item):
                        item.embedding_synced = True
                        db.session.commit()
                        success += 1
                    else:
                        fail += 1
                except Exception as e:
                    print(f"Sync Fail {item.name}: {e}")
                    fail += 1
            print(f"--- [Background] Sync Finished. Success: {success}, Fail: {fail} ---")

    # Launch Thread
    app_obj = current_app._get_current_object()
    thread = threading.Thread(target=run_sync, args=(app_obj,))
    thread.start()
            
    flash(f"Sync process started in background. The dashboard alert will disappear once complete.", "success")
    return redirect(url_for('admin.dashboard'))
