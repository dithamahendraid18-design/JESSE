from flask import render_template
from . import bp
from app.models import InteractionLog, MenuItem
from app.services.analytics import AnalyticsService
from app.extensions import db
from sqlalchemy import text

@bp.route('/dashboard')
def dashboard():
    stats = AnalyticsService.get_dashboard_stats()
    
    # Global Live Feed
    recent_logs = InteractionLog.query.order_by(InteractionLog.timestamp.desc()).limit(15).all()
    
    # Top Performing Assets (Clients by interaction volume) - Optimized
    top_clients = AnalyticsService.get_top_clients(limit=5)
    
    # Sync Check
    unsynced_count = MenuItem.query.filter((MenuItem.embedding_synced == False) | (MenuItem.embedding_synced == None)).count()

    return render_template('admin/dashboard.html', 
                           stats=stats,
                           recent_logs=recent_logs,
                           top_clients=top_clients,
                           unsynced_count=unsynced_count,
                           active_page='dashboard')

@bp.route('/logs')
def system_logs():
    return render_template('admin/logs.html', active_page='logs')

@bp.route('/fix-db-schema')
def fix_db_schema():
    # Kept for manual invocation if needed, though hotfixes are gone
    from .auth import is_logged_in
    from flask import redirect, url_for
    
    if not is_logged_in():
        return redirect(url_for('admin.login'))
        
    try:
        results = []
        
        # 1. Attempt Alembic Migration (Recommended)
        from flask_migrate import upgrade
        try:
            upgrade()
            results.append("🚀 Alembic Upgrade: Success")
        except Exception as mig_err:
            results.append(f"ℹ️ Alembic Skip/Fail: {str(mig_err)}")

        # 2. Manual SQL Fallback (Safety Layer)
        with db.engine.connect() as conn:
            # ... existing manual migrations ...
                ('clients', 'parking_info', 'TEXT', None),
                ('clients', 'direction_note', 'TEXT', None),
                ('clients', 'whatsapp_url', 'VARCHAR(255)', None),
                ('clients', 'tiktok_url', 'VARCHAR(255)', None),
                ('clients', 'youtube_url', 'VARCHAR(255)', None),
                ('clients', 'font_style', "VARCHAR(50)", "DEFAULT 'Modern Sans'"),
                ('clients', 'operating_hours', 'TEXT', None),
                ('clients', 'total_seating', 'INTEGER', None),
                ('clients', 'max_group_size', 'INTEGER', None),
                ('clients', 'seating_configuration', 'TEXT', None),
                ('clients', 'private_room_capacity', 'INTEGER', None),
                ('clients', 'has_private_room', 'BOOLEAN', 'DEFAULT FALSE'),
                ('clients', 'facilities_list', 'TEXT', None),
                ('clients', 'family_facilities_list', 'TEXT', None),
                ('clients', 'deposit_policy', 'TEXT', None),
                ('clients', 'late_arrival_policy', 'TEXT', None),
                ('menu_items', 'spiciness_level', 'INTEGER', "DEFAULT 0"),
                ('menu_items', 'prep_time', 'TEXT', None),
                ('menu_items', 'portion_size', 'VARCHAR(100)', None),
                ('knowledge_base', 'personality_tone', 'VARCHAR(50)', "DEFAULT 'friendly'"),
                ('knowledge_base', 'personality_emoji', 'VARCHAR(50)', "DEFAULT 'minimal'"),
                ('knowledge_base', 'personality_length', 'VARCHAR(50)', "DEFAULT 'concise'"),
                ('knowledge_base', 'temperature', 'FLOAT', "DEFAULT 0.7"),
                ('knowledge_base', 'max_tokens', 'INTEGER', "DEFAULT 1024"),
                ('clients', 'tos_url', 'VARCHAR(255)', None),
                ('clients', 'show_ai_disclaimer', 'BOOLEAN', 'DEFAULT TRUE'),
                ('knowledge_base', 'holiday_dates', 'TEXT', None),
                ('knowledge_base', 'use_last_order_buffer', 'BOOLEAN', 'DEFAULT FALSE'),
                ('knowledge_base', 'last_order_buffer', 'INTEGER', 'DEFAULT 0'),
                ('knowledge_base', 'handoff_notifications', 'TEXT', None),
                ('knowledge_base', 'handoff_reply', 'TEXT', None),
                ('knowledge_base', 'tax_info', 'TEXT', None),
                ('menu_items', 'embedding_synced', 'BOOLEAN', 'DEFAULT FALSE'),
            ]

            for table, col, col_type, default in migrations:
                try:
                    sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                    if default:
                        sql += f" {default}"
                    conn.execute(text(sql))
                    conn.commit()
                    results.append(f"✅ Added {col}")
                except Exception as e:
                    conn.rollback()
                    err = str(e).lower()
                    if "duplicate" in err or "exists" in err:
                        results.append(f"ℹ️  {col} already exists")
                    else:
                         results.append(f"⚠️  Error {col}: {str(e)}")
                         
        return "<br>".join(results)
    except Exception as e:
        return f"CRITICAL ERROR: {str(e)}", 500
