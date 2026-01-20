import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'jesse_saas'))

from jesse_saas.app import create_app
from jesse_saas.app.extensions import db

app = create_app()

with app.app_context():
    print(f"Using DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
    try:
        # Check if column exists using SQLAlchemy inspection
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('menu_items')]
        
        if 'allergy_info' not in columns:
            print("Column 'allergy_info' missing. Adding...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE menu_items ADD COLUMN allergy_info TEXT"))
                conn.commit()
            print("Success: Column added via Flask-SQLAlchemy.")
        else:
            print("Info: Column 'allergy_info' already exists (verified via Flask).")
            
    except Exception as e:
        print(f"Error: {e}")
