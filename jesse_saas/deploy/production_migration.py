from app import create_app, db
from sqlalchemy import text
import sys

def run_migration():
    print("🚀 Starting Production Database Migration...")
    app = create_app()
    
    with app.app_context():
        # Print DB Info (Masked password)
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"📡 Connected to: {db_url.split('@')[-1] if '@' in db_url else 'SQLite'}")
        
        with db.engine.connect() as conn:
            # List of columns to check and add
            # Format: (table, column, type, default_value_clause)
            migrations = [
                # ID & Contact
                ('clients', 'parking_info', 'TEXT', None),
                ('clients', 'direction_note', 'TEXT', None),
                ('clients', 'whatsapp_url', 'VARCHAR(255)', None), # Replaces whatsapp_number
                
                # Socials
                ('clients', 'tiktok_url', 'VARCHAR(255)', None),
                ('clients', 'youtube_url', 'VARCHAR(255)', None),
                
                # Branding & Regional
                ('clients', 'font_style', "VARCHAR(50)", "DEFAULT 'Modern Sans'"),
                ('clients', 'operating_hours', 'TEXT', None),
            ]

            for table, col, col_type, default in migrations:
                try:
                    # Check if column exists logic varies by DB, simpler to try ADD and ignore specific error
                    # or use specific inspection. For safety script, try/except is robust.
                    sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                    if default:
                        sql += f" {default}"
                    
                    conn.execute(text(sql))
                    print(f"✅ Added column: {col}")
                except Exception as e:
                    err = str(e).lower()
                    if "duplicate column" in err or "already exists" in err:
                        print(f"ℹ️  Column already exists: {col}")
                    else:
                        print(f"⚠️  Error adding {col}: {e}")
            
            # Special Case: Remove old 'whatsapp_number' if it exists? 
            # Better to leave it for safety, but we can log it.
            print("Migration run finished.")
            conn.commit()

if __name__ == "__main__":
    run_migration()
