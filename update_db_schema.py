import sqlite3

def add_column():
    db_path = r'c:\JESSE.01\jesse_saas\site.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(menu_items);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'allergy_info' not in column_names:
            print("Adding allergy_info column...")
            cursor.execute("ALTER TABLE menu_items ADD COLUMN allergy_info TEXT")
            conn.commit()
            print("Success: Column added.")
        else:
            print("Info: Column already exists.")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_column()
