from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN whatsapp_number VARCHAR(50)"))
            print("Added whatsapp_number column")
        except Exception as e:
            print(f"Skipped whatsapp_number: {e}")
            
    print("Migration complete")
