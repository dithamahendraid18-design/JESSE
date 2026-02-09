from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from . import bp
from app.models import Client, KnowledgeBase
from app.services.analytics import AnalyticsService
from app.services.client_manager import ClientManager
from app.extensions import db
from datetime import datetime
import io
import qrcode
import qrcode.image.svg

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

@bp.route('/client/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        name = request.form['restaurant_name']
        plan_type = request.form['plan_type']
        status = request.form.get('status', 'active')
        theme_color = request.form.get('theme_color', '#000000')
        logo = request.files.get('avatar')
        
        new_client = ClientManager.create_client(
            restaurant_name=name, 
            plan_type=plan_type,
            status=status,
            theme_color=theme_color,
            logo_file=logo
        )
        flash(f'Client {name} created successfully.', 'success')
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
    target_url = f"{request.host_url}chat/{client.slug or client.public_id}"
    
    fmt = request.args.get('format', 'svg')
    
    try:
        buf = io.BytesIO()
        
        if fmt == 'svg':
            # Ensure submodule is loaded (globally)
            factory = qrcode.image.svg.SvgPathImage
            img = qrcode.make(target_url, image_factory=factory)
            img.save(buf)
            mimetype = 'image/svg+xml'
            
        else:
            # Standard QR (PIL) for PNG/JPG
            img = qrcode.make(target_url)
            
            if fmt == 'jpeg':
                # Convert RGBA to RGB for JPEG
                img = img.convert("RGB") 
                img.save(buf, format='JPEG')
                mimetype = 'image/jpeg'
            else:
                # Default to PNG
                img.save(buf, format='PNG')
                mimetype = 'image/png'
        
        buf.seek(0)
        return send_file(buf, mimetype=mimetype)
        
    except Exception as e:
        print(f"QR GENERATION ERROR: {str(e)}")
        # Return a text error visible in browser if visited directly
        return f"Error generating QR: {str(e)}", 500

@bp.route('/client/<int:client_id>/stats')
@bp.route('/client/<int:client_id>/stats/<view_mode>')
def client_stats(client_id, view_mode='overview'):
    client = Client.query.get_or_404(client_id)
    from app.models import InteractionLog # Ensure import availability if context variable issue
    
    if view_mode == 'export_csv':
        csv_data = AnalyticsService.get_export_csv(client.id)
        
        from flask import Response
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=logs_{client.restaurant_name}_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )

    if view_mode not in ['overview', 'conversations', 'events', 'trends', 'reports']:
        view_mode = 'overview'
    
    context = {}
    
    if view_mode == 'overview':
        context = AnalyticsService.get_client_overview(client.id)
    
    elif view_mode == 'conversations':
        context['logs'] = client.logs.order_by(InteractionLog.timestamp.desc()).limit(50).all()

    elif view_mode == 'events':
        # Still doing this inline for now as it wasn't strictly moved, but we can iterate.
        # Ideally this should be in Service too, but sticking to plan scope.
        context['events_breakdown'] = {
            'Menu Clicks': client.logs.filter(InteractionLog.interaction_type == 'button_click', InteractionLog.user_query.ilike('%menu%')).count(),
            'Location Clicks': client.logs.filter(InteractionLog.interaction_type == 'button_click', InteractionLog.user_query.ilike('%location%')).count(),
            'Contact Clicks': client.logs.filter(InteractionLog.interaction_type == 'button_click', InteractionLog.user_query.ilike('%contact%')).count()
        }
        
    elif view_mode == 'trends':
        context['trend_data'] = AnalyticsService.get_trend_data(client.id)

    return render_template('admin/analytics.html', client=client, view_mode=view_mode, active_page=view_mode, **context)
