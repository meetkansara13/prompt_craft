"""
app/models/prompt_models.py
============================
Pydantic models for the Prompt Generator.
Used for request validation AND as typed response shapes.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── REQUEST ───────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    goal: str = Field(..., min_length=10, max_length=4000)
    model: str = Field(default="claude")
    category: str = Field(default="auto")
    output_format: str = Field(default="auto")
    complexity: str = Field(default="auto")
    tones: list[str] = Field(default_factory=lambda: ["professional"])
    framework: str = Field(default="RISEN")
    techniques: list[str] = Field(default_factory=list)
    cheat_codes: list[str] = Field(default_factory=list)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        allowed = {"claude", "chatgpt", "gpt5", "gemini", "deepseek", "grok", "universal"}
        if v not in allowed:
            raise ValueError(f"model must be one of {allowed}")
        return v

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        allowed = {"RISEN","COAST","BROKE","ROSES","CARE","RACE","TRACE","PTCF","RTF","APE","chain"}
        if v not in allowed:
            raise ValueError(f"framework must be one of {allowed}")
        return v


class RefineRequest(BaseModel):
    current_prompt: str = Field(..., min_length=10, max_length=8000)
    feedback: str = Field(..., min_length=3, max_length=2000)


# ── RESPONSE ──────────────────────────────────────────────────────────────────

class QualityScore(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: str
    clarity: int = Field(ge=0, le=100)
    specificity: int = Field(ge=0, le=100)
    technique_use: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    improvements: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    detected_intent: str
    task_type: str
    detected_domain: str
    complexity: str
    key_requirements: list[str]
    ambiguities_resolved: list[str] = Field(default_factory=list)


class PromptSections(BaseModel):
    system_context: str
    context_background: str
    main_task: str
    examples_format: str
    constraints_rules: str
    self_check: str


class ModelTip(BaseModel):
    icon: str
    title: str
    desc: str
    code: Optional[str] = None


class Explanation(BaseModel):
    icon: str
    color: str
    title: str
    desc: str


class ModelVariants(BaseModel):
    claude: str
    chatgpt: str
    gemini: str
    gpt5: str
    deepseek: str
    grok: str
    universal: str


class GenerateResponse(BaseModel):
    analysis: AnalysisResult
    quality_score: QualityScore
    prompt_sections: PromptSections
    final_prompt: str
    token_optimized_prompt: str
    model_variants: ModelVariants
    model_tips: dict[str, list[ModelTip]]
    explanations: list[Explanation]


class RefineResponse(BaseModel):
    improved_prompt: str
    token_optimized_prompt: str
    changes_made: list[str]
    quality_score: QualityScore
