from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        print("Adding Menu Item Details columns...")
        
        columns_to_add = [
            "ALTER TABLE menu_items ADD COLUMN spiciness_level INTEGER DEFAULT 0",
            "ALTER TABLE menu_items ADD COLUMN prep_time TEXT"
        ]

        for sql in columns_to_add:
            try:
                conn.execute(text(sql))
                print(f"✅ Success: {sql}")
            except Exception as e:
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    print(f"ℹ️  Skipped (exists): {sql}")
                else:
                    print(f"⚠️  Error executing '{sql}': {e}")
        
        print("Migration attempts finished.")
        conn.commit()
