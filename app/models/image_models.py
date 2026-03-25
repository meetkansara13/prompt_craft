"""
app/models/image_models.py
============================
Pydantic models for the Image → Prompt feature.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ImageAnalyzeRequest(BaseModel):
    image_base64: str = Field(..., min_length=100)
    image_type: str = Field(default="image/jpeg")
    framework: str = Field(default="react")
    prompt_type: str = Field(default="build")

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        allowed = {"react", "nextjs", "vue", "html", "tailwind", "flutter"}
        if v not in allowed:
            raise ValueError(f"framework must be one of {allowed}")
        return v

    @field_validator("prompt_type")
    @classmethod
    def validate_prompt_type(cls, v: str) -> str:
        allowed = {"build", "improve", "describe"}
        if v not in allowed:
            raise ValueError(f"prompt_type must be one of {allowed}")
        return v


class ComponentInfo(BaseModel):
    name: str
    description: str
    count: int = 1


class ColorInfo(BaseModel):
    role: str
    hex_value: str
    usage: str


class VisualAnalysis(BaseModel):
    page_type: str
    layout_structure: str
    navigation_type: str
    color_scheme: list[ColorInfo]
    typography_style: str
    border_radius_style: str
    shadow_depth: str
    spacing_density: str
    is_dark_mode: bool
    is_responsive: bool
    components_detected: list[ComponentInfo]
    interactions_detected: list[str]
    content_sections: list[str]
    target_audience: str
    primary_cta: str


class ImagePromptResponse(BaseModel):
    analysis: VisualAnalysis
    generated_prompt: str
    token_estimate: int
    framework_used: str
    prompt_type: str
    key_features: list[str]
    build_complexity: str
    tips: list[str]
