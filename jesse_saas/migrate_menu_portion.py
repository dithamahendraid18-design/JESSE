from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        print("Adding Portion Size column...")
        
        try:
            sql = "ALTER TABLE menu_items ADD COLUMN portion_size VARCHAR(100)"
            conn.execute(text(sql))
            print(f"✅ Success: {sql}")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                print(f"ℹ️  Skipped (exists): portion_size")
            else:
                print(f"⚠️  Error: {e}")
        
        conn.commit()
        print("Done.")
