"""
app/models/history_models.py
=============================
Pydantic models for the History module.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    id: int
    timestamp: str
    goal: str
    model: str
    framework: str
    score: int
    prompt: str
    full_data: dict[str, Any] = Field(default_factory=dict)


class HistoryListItem(BaseModel):
    """Lightweight entry for the list view (no full_data)."""
    id: int
    timestamp: str
    goal: str
    model: str
    framework: str
    score: int


class SaveHistoryRequest(BaseModel):
    goal: str = Field(..., max_length=500)
    model: str
    framework: str
    score: int = Field(ge=0, le=100)
    prompt: str
    full_data: dict[str, Any] = Field(default_factory=dict)
