from __future__ import annotations

from flask import jsonify


class JesseError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(JesseError)
    def handle_jesse_error(err: JesseError):
        return jsonify({"error": str(err)}), err.status_code

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Internal server error"}), 500
