import sqlite3

def inspect_db():
    try:
        db_path = r'c:\JESSE.01\jesse_saas\site.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"--- Schema for menu_items in {db_path} ---")
        cursor.execute("PRAGMA table_info(menu_items);")
        columns = cursor.fetchall()
        for col in columns:
            if col[1] == 'price':
                print(f"Verified Column: {col[1]} is type {col[2]}")

        print("\n--- Recent Menu Items (Name, Price) ---")
        cursor.execute("SELECT name, price FROM menu_items ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Item: {row[0]}, Price: {row[1]}, Type: {type(row[1])}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
