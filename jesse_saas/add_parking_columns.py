from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN parking_info TEXT"))
            print("Added parking_info column")
        except Exception as e:
            print(f"Skipped parking_info: {e}")

        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN direction_note TEXT"))
            print("Added direction_note column")
        except Exception as e:
            print(f"Skipped direction_note: {e}")
            
    print("Migration complete")
