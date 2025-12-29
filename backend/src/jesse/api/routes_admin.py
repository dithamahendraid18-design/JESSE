from __future__ import annotations

from typing import Tuple
from flask import Blueprint, jsonify, request, Response

from ..database import db
from ..orm import Client, MenuItem, MenuCategory
from ..core.errors import JesseError

bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")

ADMIN_PASSWORD = "secret-password"

def _check_admin_auth():
    """Simple hardcoded password check."""
    pwd = request.headers.get("X-Admin-Password")
    if pwd != ADMIN_PASSWORD:
        raise JesseError("Unauthorized: Invalid Admin Password", 401)

@bp.get("/version")
def version():
    return jsonify({"version": "0.1.0"})

@bp.get("/clients")
def list_clients():
    _check_admin_auth()
    clients = db.session.query(Client).all()
    data = []
    for c in clients:
        data.append({
            "id": c.id,
            "name": c.name,
            "plan_type": c.plan_type,
            "updated_at": "now" # Placeholder
        })
    return jsonify(data)

@bp.get("/clients/<client_id>/menu")
def get_client_menu(client_id: str):
    _check_admin_auth()
    
    # Verify client exists
    client = db.session.query(Client).get(client_id)
    if not client:
        raise JesseError("Client not found", 404)

    # Fetch categories and items
    categories = db.session.query(MenuCategory).filter_by(client_id=client_id).all()
    
    result = []
    for cat in categories:
        items = []
        for item in cat.items:
            items.append({
                "id": item.id,
                "name": item.name,
                "price": item.price,
                "desc": item.desc,
                "image": item.image
            })
        result.append({
            "id": cat.id,
            "category_id": cat.category_id,
            "label": cat.label,
            "items": items
        })
        
    return jsonify(result)

@bp.put("/menu-items/<int:item_id>")
def update_menu_item(item_id: int):
    _check_admin_auth()
    
    data = request.json or {}
    item = db.session.query(MenuItem).get(item_id)
    if not item:
        raise JesseError("Menu item not found", 404)

    # Update allowed fields
    if "price" in data:
        try:
            item.price = float(data["price"])
        except ValueError:
            raise JesseError("Invalid price format", 400)
            
    if "desc" in data:
        item.desc = str(data["desc"])
        
    if "name" in data:
        item.name = str(data["name"])

    db.session.commit()
    
    return jsonify({"status": "updated", "item": {
        "id": item.id,
        "name": item.name,
        "price": item.price,
        "desc": item.desc
    }})
