"""
app/api/routes/history_routes.py
===================================
Blueprint for prompt history management.
Routes:
  POST /api/history/save
  GET  /api/history/list
  GET  /api/history/<id>
  POST /api/history/clear
"""

from flask import Blueprint, request, jsonify, session
from pydantic import ValidationError

from app.models.history_models import SaveHistoryRequest
from app.services.history_service import HistoryService
from app.utils.errors import HistoryNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint("history", __name__, url_prefix="/api/history")


@bp.post("/save")
def save():
    data = request.get_json(silent=True) or {}
    try:
        req = SaveHistoryRequest(**data)
    except ValidationError as exc:
        return jsonify({"error": str(exc.errors()[0].get("msg", "Invalid"))}), 400

    svc     = HistoryService(session)
    entry_id = svc.save(req)
    return jsonify({"ok": True, "id": entry_id})


@bp.get("/list")
def list_entries():
    svc   = HistoryService(session)
    items = svc.list_entries()
    return jsonify({"items": [i.model_dump() for i in items]})


@bp.get("/<int:entry_id>")
def get_entry(entry_id: int):
    try:
        svc   = HistoryService(session)
        entry = svc.get_entry(entry_id)
        return jsonify({"ok": True, "item": entry.model_dump()})
    except HistoryNotFoundError as exc:
        return jsonify({"ok": False, "error": exc.message}), 404


@bp.post("/clear")
def clear():
    HistoryService(session).clear()
    return jsonify({"ok": True})
