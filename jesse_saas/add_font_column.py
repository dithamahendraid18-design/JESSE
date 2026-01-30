from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN font_style VARCHAR(50) DEFAULT 'Modern Sans'"))
            print("Added font_style column")
        except Exception as e:
            print(f"Skipped font_style: {e}")
            
    print("Migration complete")
