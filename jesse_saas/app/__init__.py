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

    # Auto-create tables & Fix Schema for Vercel
    with app.app_context():
        db.create_all()
        
        # ---------------------------------------------------------
        # HOTFIX: Auto-Migrate columns if missing
        # ---------------------------------------------------------
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            if 'menu_items' in inspector.get_table_names():
                cols = [c['name'] for c in inspector.get_columns('menu_items')]
                
                # Migrate allergy_info
                if 'allergy_info' not in cols:
                    print("⚠️ Migration: Adding missing 'allergy_info' column...")
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE menu_items ADD COLUMN allergy_info VARCHAR(255)"))
                        conn.commit()
                    print("✅ Migration: 'allergy_info' added.")

                # Migrate original_price
                if 'original_price' not in cols:
                    print("⚠️ Migration: Adding missing 'original_price' column...")
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE menu_items ADD COLUMN original_price FLOAT"))
                        conn.commit()
                    print("✅ Migration: 'original_price' added.")

                # Migrate labels
                if 'labels' not in cols:
                    print("⚠️ Migration: Adding missing 'labels' column...")
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE menu_items ADD COLUMN labels VARCHAR(255)"))
                        conn.commit()
                    print("✅ Migration: 'labels' added.")
                    
        except Exception as e:
            print(f"❌ Migration Error: {e}")
        # ---------------------------------------------------------

    # Register Blueprints
    from .api.routes import bp as api_bp
    app.register_blueprint(api_bp)

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
            return UploadService.resolve_url(filename, width=width)
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

        # Sort Categories based on KB order
        import json
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

        return render_template(
            'menu/public.html',
            client=client,
            menu_by_cat=menu_by_cat,
            sorted_categories=sorted_categories,
            currency=client.currency_symbol or '$',
            theme_color=client.theme_color or '#2563EB'
        )

    return app
