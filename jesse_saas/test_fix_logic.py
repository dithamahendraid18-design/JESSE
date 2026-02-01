from app import create_app, db
from sqlalchemy import text
import sys

def test_fix_logic():
    print("🧪 Testing Fix Logic...")
    app = create_app()
    
    with app.app_context():
        # Create a dummy table if needed or just use clients
        # We'll try to add a dummy column 'test_col' to clients to see if the logic holds
        
        try:
             with db.engine.connect() as conn:
                print("Connected to DB.")
                
                # logic from route
                col = "test_col_emergency"
                table = "clients"
                col_type = "VARCHAR(50)"
                
                try:
                    sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                    print(f"Executing: {sql}")
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Added {col}")
                except Exception as e:
                    conn.rollback()
                    print(f"⚠️  Error adding {col}: {e}")
                    
                # Clean up
                try:
                    conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {col}"))
                    conn.commit()
                    print("Cleaned up.")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    test_fix_logic()
