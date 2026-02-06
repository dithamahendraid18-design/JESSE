import sqlite3
import os
from app import create_app

app = create_app()
db_uri = app.config['SQLALCHEMY_DATABASE_URI']
print(f"Flask Config DB URI: {db_uri}")

if db_uri.startswith('sqlite:///'):
    path = db_uri.replace('sqlite:///', '')
    print(f"Target DB Path: {path}")
    
    if os.path.exists(path):
        print(f"File exists: {path} (Size: {os.path.getsize(path)} bytes)")
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        print("\n--- RAW SQL DUMP (Clients) ---")
        try:
            cur.execute("SELECT id, restaurant_name, public_id, slug FROM clients")
            rows = cur.fetchall()
            for r in rows:
                print(r)
        except Exception as e:
            print(f"SQL Error: {e}")
        conn.close()
    else:
        print(f"FILE NOT FOUND at {path}")
else:
    print("Not using SQLite.")
