
import os
import shutil
import uuid
from pathlib import Path
from flask import Flask
from jesse.app import create_app
from jesse.database import db
from jesse.orm import Client, MenuItem, AboutCard
from sqlalchemy import select

def migrate():
    print("🔹 STARTING ASSET MIGRATION 🔹")
    app = create_app()
    
    with app.app_context():
        clients = db.session.query(Client).all()
        base_dir = Path("clients") # backend/clients
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        for client in clients:
            print(f"Processing Client: {client.name} ({client.id})")
            client_dir = base_dir / client.id
            public_assets_dir = client_dir / "assets" / "public"
            
            # Helper to move file
            def move_and_update(old_url):
                if not old_url: return None
                if old_url.startswith("/uploads/"): return old_url # Already moved
                
                # Determine local filename
                # Case 1: /client-assets/<cid>/filename.png
                # Case 2: filename.png (legacy relative)
                
                filename = None
                if old_url.startswith("/client-assets/"):
                    parts = old_url.split("/")
                    # /client-assets/luna_002/pic.png -> parts[-1] = pic.png
                    # BUT wait, the route is /client-assets/<client_id>/<filename>
                    # IF the url is constructed correctly.
                    # Sometimes old data might be just "pic.png" and FE prepends?
                    # Let's assume standard full URL stored or relative.
                    
                    # If matches current client ID
                    if f"/client-assets/{client.id}/" in old_url:
                        filename = old_url.split("/")[-1]
                elif not "/" in old_url:
                     filename = old_url
                
                if not filename:
                    # Could be external URL or other client?
                    if old_url.startswith("http"): return old_url
                    print(f"  [WARN] Skipping unknown URL format: {old_url}")
                    return old_url

                # Attempt to find file
                src_path = public_assets_dir / filename
                if not src_path.exists():
                     # Try regular assets dir?
                     src_path = client_dir / "assets" / filename
                
                if not src_path.exists():
                    print(f"  [MISS] File not found: {src_path} (URL: {old_url})")
                    return old_url # Keep as is, maybe it works somehow or is lost
                
                # Copy file
                # Use unique name to avoid collisions
                ext = src_path.suffix
                new_filename = f"{client.id}_{uuid.uuid4().hex[:6]}{ext}"
                dest_path = upload_dir / new_filename
                
                try:
                    shutil.copy2(src_path, dest_path)
                    new_url = f"/uploads/{new_filename}"
                    print(f"  [MOVE] {filename} -> {new_url}")
                    return new_url
                except Exception as e:
                    print(f"  [ERR] Failed to copy {src_path}: {e}")
                    return old_url

            # 1. Update Profile Image
            if client.profile_image_url:
                new_url = move_and_update(client.profile_image_url)
                if new_url != client.profile_image_url:
                    client.profile_image_url = new_url
            
            # 2. Update Bot Avatar
            if client.bot_avatar_url:
                new_url = move_and_update(client.bot_avatar_url)
                if new_url != client.bot_avatar_url:
                    client.bot_avatar_url = new_url

            # 3. Update Menu Items
            # Need to traverse categories?
            # Or direct query?
            # MenuItem has image_url (new) and image (legacy)
            # We should migrate 'image' to 'image_url' if missing, and update path.
            
            # Helper to find items for this client is hard via pure SQL if relationship is indirect via Category
            # But we have ORM relationships.
            for cat in client.menu_categories:
                for item in cat.items:
                    # Prefer image_url, fallback to image
                    # Existing migration might have populated image_url from image? 
                    # If image_url is set, use it. If not, check image.
                    
                    target_val = item.image_url or item.image
                    if target_val:
                        new_url = move_and_update(target_val)
                        # Always set the NEW field 'image_url'
                        if new_url != item.image_url:
                            item.image_url = new_url
                            # Optional: Clear old 'image' field or leave for backwards compat?
                            # Let's leave it but ensure we use image_url in FE.

            # 4. Update About Cards
            for card in client.about_cards:
                 if card.image_url:
                    new_url = move_and_update(card.image_url)
                    if new_url != card.image_url:
                        card.image_url = new_url

        db.session.commit()
        print("✅ MIGRATION COMPLETE. Database updated.")

if __name__ == "__main__":
    migrate()
