
from jesse.app import create_app
from jesse.database import db
from jesse.orm import Client
import sqlalchemy

def migrate():
    print("🔹 MIGRATING SYSTEM PROMPTS...")
    app = create_app()
    with app.app_context():
        # Check if column exists, if not add it (SQLite hack)
        with db.engine.connect() as conn:
            try:
                conn.execute(sqlalchemy.text("ALTER TABLE clients ADD COLUMN system_prompt TEXT"))
                print("✅ Added 'system_prompt' column.")
            except Exception as e:
                print(f"ℹ️ Column might already exist: {e}")

        clients = db.session.query(Client).all()
        for c in clients:
            # Try to load from file
            # clients/<id>/prompts/system.md
            try:
                path = f"clients/{c.id}/prompts/system.md"
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    c.system_prompt = content
                    print(f"✅ Loaded prompt for {c.name}")
            except FileNotFoundError:
                print(f"⚠️ No system.md for {c.name}, using default.")
                c.system_prompt = "You are a helpful assistant."
        
        db.session.commit()
        print("✅ System Prompts Saved to DB.")

if __name__ == "__main__":
    migrate()
