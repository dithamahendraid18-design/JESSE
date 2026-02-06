import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app.extensions import db
from sqlalchemy import text

with app.app_context():
    print("Dropping menu_embeddings table...")
    try:
        db.session.execute(text("DROP TABLE IF EXISTS menu_embeddings CASCADE"))
        db.session.commit()
        print("Dropped.")
    except Exception as e:
        print(f"Error dropping table: {e}")
