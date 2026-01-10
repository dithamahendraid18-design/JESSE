import sqlite3
import os

DB_PATH = "instance/jesse.db"

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add profile_image_url to clients table
        print("Migrating clients table...")
        try:
            cursor.execute("ALTER TABLE clients ADD COLUMN profile_image_url TEXT")
            print("✅ Added profile_image_url to clients table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️  profile_image_url already exists in clients table")
            else:
                raise e

        # Add image_url to menu_items table
        print("Migrating menu_items table...")
        try:
            cursor.execute("ALTER TABLE menu_items ADD COLUMN image_url TEXT")
            print("✅ Added image_url to menu_items table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️  image_url already exists in menu_items table")
            else:
                raise e

        conn.commit()
        print("🚀 Migration for images completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
