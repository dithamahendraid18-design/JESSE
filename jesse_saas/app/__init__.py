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

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory, current_app
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    @app.route('/')
    def index():
        return "JESSE SaaS Backend Active. Go to /admin/login."

    @app.route('/favicon.ico')
    def favicon():
        return "", 204

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
