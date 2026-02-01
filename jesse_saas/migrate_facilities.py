from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
            print("Adding Facilities & Capacity columns...")
            
            columns_to_add = [
                "ALTER TABLE clients ADD COLUMN total_seating INTEGER",
                "ALTER TABLE clients ADD COLUMN max_group_size INTEGER",
                "ALTER TABLE clients ADD COLUMN seating_configuration TEXT", # New
                "ALTER TABLE clients ADD COLUMN private_room_capacity INTEGER",
                "ALTER TABLE clients ADD COLUMN has_private_room BOOLEAN DEFAULT 0",
                "ALTER TABLE clients ADD COLUMN facilities_list TEXT",
                "ALTER TABLE clients ADD COLUMN family_facilities_list TEXT",
                "ALTER TABLE clients ADD COLUMN deposit_policy TEXT",
                "ALTER TABLE clients ADD COLUMN late_arrival_policy TEXT"
            ]

            for sql in columns_to_add:
                try:
                    conn.execute(text(sql))
                    print(f"✅ Success: {sql}")
                except Exception as e:
                    # Check if it's just a duplicate column error
                    msg = str(e).lower()
                    if "duplicate column" in msg or "already exists" in msg:
                        print(f"ℹ️  Skipped (exists): {sql}")
                    else:
                        print(f"⚠️  Error executing '{sql}': {e}")
            
            print("Migration attempts finished.")
            
    print("Done.")
