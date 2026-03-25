"""
app/models/optimizer_models.py
================================
Pydantic models for the Token Optimizer.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── REQUEST ───────────────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=8000)
    target_model: str = Field(default="universal")
    level: str = Field(default="balanced")
    sensitivity: str = Field(default="general")
    techniques: list[str] = Field(default_factory=lambda: [
        "semantic", "structure", "cod", "filler", "negative", "primacy"
    ])

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"balanced", "aggressive", "ultra"}
        if v not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v


# ── RESPONSE ──────────────────────────────────────────────────────────────────

class TokenBreakdownItem(BaseModel):
    category: str
    tokens: int
    pct: float
    color: str


class WasteIssue(BaseModel):
    severity: str   # high | medium | low | info
    icon: str
    title: str
    desc: str
    save: Optional[str] = None


class TokenAnalysis(BaseModel):
    original_tokens: int
    waste_pct: float
    token_breakdown: list[TokenBreakdownItem]
    issues: list[WasteIssue]


class OptimizedVersion(BaseModel):
    prompt: str
    tokens: int
    pct: float          # % reduction from original
    techniques: list[str]


class OptimizedVersions(BaseModel):
    balanced: OptimizedVersion
    aggressive: OptimizedVersion
    ultra: OptimizedVersion


class QualityMetrics(BaseModel):
    semantic_retention: float
    intent_clarity: float
    readability: float
    accuracy_risk: float


class SavingsEstimate(BaseModel):
    tokens_saved: int
    cost_pct: float
    speed_pct: float
    example: str


class TechniqueApplied(BaseModel):
    icon: str
    name: str
    desc: str
    saved: int


class ModelTip(BaseModel):
    icon: str
    title: str
    desc: str
    code: Optional[str] = None


class OptimizeResponse(BaseModel):
    analysis: TokenAnalysis
    versions: OptimizedVersions
    quality: QualityMetrics
    savings: SavingsEstimate
    techniques_applied: list[TechniqueApplied]
    model_tips: dict[str, list[ModelTip]]
