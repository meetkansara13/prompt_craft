"""
app/services/history_service.py
=================================
Manages prompt history stored in the Flask session.

Cookie size fix: full_data (entire LLM response with all 7 model variants)
was stored in the session cookie, bloating it past the 4093-byte browser limit.

Fix: store only essential lightweight fields in session.
     full_data is stripped to just the fields needed to reload a prompt:
     final_prompt, token_optimized_prompt, model_variants, quality_score.
     Everything else (explanations, diagram_data, analysis) is dropped.
     This keeps each history entry under ~800 bytes.
"""

from datetime import datetime

from config.settings import get_config
from app.models.history_models import HistoryEntry, HistoryListItem, SaveHistoryRequest
from app.utils.errors import HistoryNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)
_cfg   = get_config()

MAX_HISTORY = _cfg.MAX_HISTORY
# Hard cap on prompt text stored per entry to prevent cookie bloat
MAX_PROMPT_CHARS  = 800
MAX_GOAL_CHARS    = 120


def _slim_full_data(full_data: dict) -> dict:
    """
    Strip full_data down to the minimum needed to reload a prompt.
    Target: < 600 bytes per entry after slimming.
    """
    if not full_data or not isinstance(full_data, dict):
        return {}

    slim = {}

    # Quality score — keep (small)
    if full_data.get("quality_score"):
        qs = full_data["quality_score"]
        slim["quality_score"] = {
            "score": qs.get("score", 0),
            "grade": qs.get("grade", ""),
        }

    # final_prompt — truncate to MAX_PROMPT_CHARS
    fp = full_data.get("final_prompt", "")
    if fp:
        slim["final_prompt"] = fp[:MAX_PROMPT_CHARS]

    # token_optimized_prompt — truncate
    tp = full_data.get("token_optimized_prompt", "")
    if tp:
        slim["token_optimized_prompt"] = tp[:MAX_PROMPT_CHARS]

    # model_variants — keep only the primary model's variant, truncated
    mv = full_data.get("model_variants")
    if mv and isinstance(mv, dict):
        # Store just 2 variants to save space
        slim["model_variants"] = {
            k: v[:400] for k, v in list(mv.items())[:2] if v
        }

    return slim


class HistoryService:
    """
    Operates on a session dict. The Flask session is passed in —
    this service never imports Flask directly.
    """

    def __init__(self, session: dict) -> None:
        self._session = session
        if "history" not in self._session:
            self._session["history"] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, req: SaveHistoryRequest) -> int:
        """
        Save a new history entry. Returns the new entry id.
        Automatically trims to MAX_HISTORY entries (newest first).
        full_data is slimmed before storing to prevent cookie overflow.
        """
        history: list[dict] = self._session["history"]

        entry_id = self._next_id(history)
        entry = {
            "id":        entry_id,
            "timestamp": datetime.now().strftime("%b %d, %H:%M"),
            "goal":      req.goal[:MAX_GOAL_CHARS],
            "model":     req.model,
            "framework": req.framework,
            "score":     req.score,
            "prompt":    req.prompt[:MAX_PROMPT_CHARS] if req.prompt else "",
            # Slim full_data — only keep what's needed to reload the prompt
            "full_data": _slim_full_data(req.full_data) if req.full_data else {},
        }

        history.insert(0, entry)

        # Trim to max entries
        if len(history) > MAX_HISTORY:
            history = history[:MAX_HISTORY]

        self._session["history"] = history
        self._session.modified = True

        logger.debug("History saved | id=%d goal=%s", entry_id, req.goal[:40])
        return entry_id

    def list_entries(self) -> list[HistoryListItem]:
        """Return lightweight list (no full_data) newest first."""
        history: list[dict] = self._session.get("history", [])
        return [
            HistoryListItem(
                id=e["id"],
                timestamp=e.get("timestamp", ""),
                goal=e.get("goal", ""),
                model=e.get("model", "claude"),
                framework=e.get("framework", ""),
                score=e.get("score", 0),
            )
            for e in history
        ]

    def get_entry(self, entry_id: int) -> HistoryEntry:
        """Return a full history entry by id."""
        history: list[dict] = self._session.get("history", [])
        for e in history:
            if e.get("id") == entry_id:
                return HistoryEntry(
                    id=e["id"],
                    timestamp=e.get("timestamp", ""),
                    goal=e.get("goal", ""),
                    model=e.get("model", "claude"),
                    framework=e.get("framework", ""),
                    score=e.get("score", 0),
                    prompt=e.get("prompt", ""),
                    full_data=e.get("full_data", {}),
                )
        raise HistoryNotFoundError(f"No history entry with id={entry_id}")

    def clear(self) -> None:
        """Delete all history entries for this session."""
        self._session["history"] = []
        self._session.modified = True
        logger.info("History cleared")

    def count(self) -> int:
        return len(self._session.get("history", []))

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _next_id(history: list[dict]) -> int:
        if not history:
            return 1
        return max(e.get("id", 0) for e in history) + 1