import os
import json
from pathlib import Path
from src.jesse.app import create_app
from src.jesse.database import db
from src.jesse.orm import Client, Theme, Channel, Response, MenuCategory, MenuItem

def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def migrate():
    # Setup App Context
    app = create_app()
    
    # Configure SQLite URI if not set (default to local file)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        db_path = Path(__file__).parent / "instance" / "jesse.db"
        db_path.parent.mkdir(exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.app_context():
        print(f"Creating database at {app.config['SQLALCHEMY_DATABASE_URI']}...")
        db.create_all()

        clients_dir = Path(__file__).parent / "clients"
        
        # Iterate over each client folder
        for client_path in clients_dir.iterdir():
            if not client_path.is_dir() or client_path.name.startswith("_"):
                continue

            client_id = client_path.name
            print(f"Migrating client: {client_id}")

            # 1. Client Info
            client_json = read_json(client_path / "client.json")
            if not client_json:
                print(f"Skipping {client_id} (missing client.json)")
                continue

            client = Client(
                id=client_id,
                name=client_json.get("name", "Unknown"),
                bot_avatar_url=client_json.get("bot_avatar_url"),
                locale=client_json.get("locale", "en-US"),
                timezone=client_json.get("timezone", "UTC"),
                public=client_json.get("public", True),
                plan_type=client_json.get("plan_type", "basic"),
                features=client_json.get("features", {}),
                currency=read_json(client_path / "assets" / "menu.json").get("currency", "USD"),
                promo=read_json(client_path / "assets" / "menu.json").get("promo", {})
            )
            db.session.merge(client) # Merge prevents duplicates on re-run

            # 2. Theme
            theme_json = read_json(client_path / "theme" / "theme.json")
            theme = Theme(
                client_id=client_id,
                brand_name=theme_json.get("brand_name"),
                primary_color=theme_json.get("primary_color"),
                bubble_color=theme_json.get("bubble_color"),
                background=theme_json.get("background"),
                text_color=theme_json.get("text_color"),
                font_family=theme_json.get("font_family"),
                bot_avatar_url=theme_json.get("bot_avatar_url")
            )
            # Find existing theme to update or add new
            existing_theme = db.session.query(Theme).filter_by(client_id=client_id).first()
            if existing_theme:
                db.session.delete(existing_theme)
            db.session.add(theme)

            # 3. Channels
            channels_json = read_json(client_path / "integrations" / "channels.json")
            existing_channel = db.session.query(Channel).filter_by(client_id=client_id).first()
            if existing_channel:
                db.session.delete(existing_channel)
            
            db.session.add(Channel(client_id=client_id, data=channels_json))

            # 4. Responses (Flatten structure: key -> json_content)
            responses_json = read_json(client_path / "assets" / "responses.json")
            
            # Clear old responses
            db.session.query(Response).filter_by(client_id=client_id).delete()
            
            # Helper to flatten intents
            def add_response(intent, content):
                db.session.add(Response(client_id=client_id, intent=intent, content=content))

            # Top level keys
            for key, val in responses_json.items():
                if key == "intents":
                    # Nested intents
                    for intent_name, intent_content in val.items():
                        add_response(intent_name, intent_content)
                else:
                    # Direct keys like 'greeting', 'main_menu'
                    add_response(key, val)

            # 5. Menu
            menu_json = read_json(client_path / "assets" / "menu.json")
            
            # Clear old menu
            db.session.query(MenuCategory).filter_by(client_id=client_id).delete()
            
            for cat in menu_json.get("categories", []):
                category = MenuCategory(
                    client_id=client_id,
                    category_id=cat.get("id"),
                    label=cat.get("label")
                )
                db.session.add(category)
                db.session.flush() # Flush to get category.id (PK)

                for item in cat.get("items", []):
                    menu_item = MenuItem(
                        category_db_id=category.id,
                        name=item.get("name"),
                        price=item.get("price", 0),
                        desc=item.get("desc"),
                        image=item.get("image"),
                        allergens=item.get("allergens", []),
                        may_contain=item.get("may_contain", [])
                    )
                    db.session.add(menu_item)

            db.session.commit()
            print(f"✅ Migrated {client_id}")

if __name__ == "__main__":
    migrate()
