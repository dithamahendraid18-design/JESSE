import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app.extensions import db
from sqlalchemy import text

if __name__ == "__main__":
    with app.app_context():
        print("ATTEMPTING DROP...")
        try:
             # Drop cascade
            db.session.execute(text("DROP TABLE IF EXISTS menu_embeddings CASCADE"))
            db.session.commit()
            print("DROP SUCCESSFUL")
        except Exception as e:
            print(f"DROP FAILED: {e}")
