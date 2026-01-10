import sqlite3
import os
from pathlib import Path

def migrate():
    print("🚀 Migrating DB: Adding 'about_cards' table...")
    
    # Path to DB
    # backend/instance/jesse.db usually
    # We are in backend/
    db_path = Path("instance") / "jesse.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS about_cards (
            id INTEGER PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL,
            image_url VARCHAR(255) NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        );
        """)
        conn.commit()
        print("✅ Table 'about_cards' created successfully.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
