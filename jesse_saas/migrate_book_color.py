import sqlite3
import os

# Database path (assuming standard Flask-SQLAlchemy default for local dev)
# It's usually app.db or site.db in the root or instance folder.
# Let's check config or try to find it. 
# Based on file structure c:\JESSE.01\jesse_saas, likely 'jesse_saas.db' or similar if not configured.
# However, usually it's best to use the app context.

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Attempting to add column book_theme_color to knowledge_base table...")
    try:
        # Check if using SQLite
        engine = db.engine
        if 'sqlite' in str(engine.url):
            with engine.connect() as conn:
                # Add columns individually for SQLite limitation handling if needed, though simple ADD COLUMN works
                try:
                    conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN book_cover_image VARCHAR(255)"))
                except Exception as e:
                    print(f"Skipping book_cover_image: {e}")
                    
                try:
                    conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN book_logo_image VARCHAR(255)"))
                except Exception as e:
                    print(f"Skipping book_logo_image: {e}")
                    
                try:
                    conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN book_cover_style VARCHAR(20) DEFAULT 'cover'"))
                except Exception as e:
                    print(f"Skipping book_cover_style: {e}")
                    
                conn.commit()
            print("Successfully added columns (SQLite).")
        else:
            # Assuming Postgres or similar
             with engine.connect() as conn:
                conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN book_cover_image VARCHAR(255)"))
                conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN book_logo_image VARCHAR(255)"))
                conn.execute(text("ALTER TABLE knowledge_base ADD COLUMN book_cover_style VARCHAR(20) DEFAULT 'cover'"))
                conn.commit()
             print("Successfully added columns (SQL).")
             
    except Exception as e:
        print(f"Migration might have failed or column exists: {e}")
