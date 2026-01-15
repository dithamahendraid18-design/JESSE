from flask import Flask
from .extensions import db, migrate, cors
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Register Models (Importing them ensures they are known to SQLAlchemy/Migrate)
    from . import models

    # Auto-create tables for SQLite fallback (Vercel) to ensure app works immediately
    # This is a safety net when not using Postgres/Migrations in production yet
    with app.app_context():
        db.create_all()

    # Register Blueprints
    from .api.routes import bp as api_bp
    app.register_blueprint(api_bp)

    from .admin.routes import bp as admin_bp
    from .admin.routes import bp as admin_bp
    app.register_blueprint(admin_bp)

    @app.route('/db-debug')
    def db_debug():
        from flask import jsonify, request
        from sqlalchemy import inspect, text
        
        status = {}
        try:
            # 1. Check Connection
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            status['connection'] = 'OK'
            
            # 2. Check Tables
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            status['tables'] = tables
            
            # 3. Force Init (Optional)
            if request.args.get('init') == 'true':
                db.create_all()
                status['init_attempt'] = 'Ran db.create_all()'
                # Refresh tables
                status['tables_after_init'] = inspect(db.engine).get_table_names()

        except Exception as e:
            status['error'] = str(e)
            return jsonify(status), 500
            
        return jsonify(status)

    # Register Template Helper for Cloudinary/Local URLs
    from app.services.upload_service import UploadService
    
    @app.context_processor
    def utility_processor():
        def resolve_file(filename, folder='', width=None):
            if not filename: return None
            
            # Check if it's a remote URL (Cloudinary)
            if UploadService.is_remote_url(filename):
                # Optimize Cloudinary URLs
                if 'cloudinary.com' in filename and '/upload/' in filename:
                    import re
                    # Default transformations: Auto format (WebP/AVIF), Auto Quality
                    transforms = ['f_auto', 'q_auto']
                    
                    if width:
                        transforms.append(f'w_{width}')
                        transforms.append('c_limit') # Resize but maintain aspect ratio (don't crop)
                    
                    transform_str = ','.join(transforms)
                    
                    # Inject transformations after /upload/
                    # Pattern: match /upload/ and replace with /upload/{transforms}/
                    return re.sub(r'(/upload/)', f'\\1{transform_str}/', filename, count=1)
                
                return filename

            # Local file logic
            from flask import url_for
            path = filename if '/' in filename else f"{folder}/{filename}"
            return url_for('uploaded_file', filename=path)
        return dict(resolve_file=resolve_file)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory, current_app
        # This route is for LOCAL dev only or Vercel /tmp fallback
        # In cloud mode, resolve_file should return the remote URL directly, never hitting this.
        upload_folder = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_folder, filename)

    @app.route('/favicon.png')
    @app.route('/favicon.ico')
    def serve_favicon():
        from flask import send_from_directory
        import os
        return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                                   'favicon.png', mimetype='image/png')

    @app.route('/')
    def index():
        return "JESSE SaaS Backend Active. Go to /admin/login."



    @app.route('/fix-db-schema')
    def fix_db_schema():
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                # Check if column exists first? Postgres safe add:
                # conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN IF NOT EXISTS category_order TEXT;"))
                conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN IF NOT EXISTS category_order TEXT;"))
                conn.commit()
            return "Schema Fixed: category_order column added."
        except Exception as e:
            return f"Error: {e}", 500

    # Standalone Chat Page (SSR Simulator)
    @app.route('/chat/<public_id>')
    def standalone_chat(public_id):
        from flask import render_template, abort
        import json
        from .models import Client, MenuItem

        # Find client by public_id (or slug if implemented, but public_id is safer initially)
        # Assuming public_id is the UUID or slug.
        client = Client.query.filter_by(public_id=public_id).first()
        if not client:
             # Fallback to slug lookup if not found
             client = Client.query.filter_by(slug=public_id).first()

        if not client:
            return "Client not found", 404

        kb = client.knowledge_base
        
        # Parse Starters JSON safely
        starters = []
        if kb and kb.conversation_starters:
            try:
                starters = json.loads(kb.conversation_starters)
            except:
                starters = []

        # Theme Defaults
        theme_color = client.theme_color or '#2563EB'
        
        # Display Mode: 'embed' or 'standalone' (default)
        from flask import request
        mode = request.args.get('mode', 'standalone')

        # Fetch Menu Data
        menu_items = MenuItem.query.filter_by(client_id=client.id, is_available=True).all()
        menu_data = [item.to_dict() for item in menu_items]

        return render_template(
            'chat/index.html',
            client=client,
            kb=kb,
            starters=starters,
            theme_color=theme_color,
            mode=mode,
            menu_data=menu_data,
            currency=client.currency_symbol,
            menu_config=kb.flow_menu if kb and kb.flow_menu else None
        )




    # Public Menu Page (Webview Target)
    @app.route('/menu/<public_id>')
    def public_menu(public_id):
        from flask import render_template
        from .models import Client, MenuItem

        client = Client.query.filter_by(public_id=public_id).first()
        if not client:
             client = Client.query.filter_by(slug=public_id).first()
        
        if not client:
            return "Client not found", 404

        menu_items = MenuItem.query.filter_by(client_id=client.id, is_available=True).all()
        # Group by Category for better display
        menu_by_cat = {}
        for item in menu_items:
            cat = item.category or 'Other'
            if cat not in menu_by_cat:
                menu_by_cat[cat] = []
            menu_by_cat[cat].append(item)

        return render_template(
            'menu/public.html',
            client=client,
            menu_by_cat=menu_by_cat,
            currency=client.currency_symbol or '$',
            theme_color=client.theme_color or '#2563EB'
        )

    return app
