from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


@bp.get("/version")
def version():
    return jsonify({"version": "0.1.0"})
