from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN tiktok_url VARCHAR(255)"))
            print("Added tiktok_url column")
        except Exception as e:
            print(f"Skipped tiktok_url: {e}")

        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN youtube_url VARCHAR(255)"))
            print("Added youtube_url column")
        except Exception as e:
            print(f"Skipped youtube_url: {e}")
            
    print("Migration complete")
