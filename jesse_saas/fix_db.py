from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Fixing Database Schema...")
    try:
        with db.engine.connect() as conn:
            # Add missing columns safely
            conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN category_order TEXT;"))
            print("Success: Added 'category_order' column.")
            conn.commit()
    except Exception as e:
        print(f"Error (probably exists): {e}")
        
    print("Done.")
