from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            # We don't drop the old column to avoid risk, just add the new one
            # The old 'whatsapp_number' will just be unused
            conn.execute(text("ALTER TABLE clients ADD COLUMN whatsapp_url VARCHAR(255)"))
            print("Added whatsapp_url column")
        except Exception as e:
            print(f"Skipped whatsapp_url: {e}")
            
    print("Migration complete")
