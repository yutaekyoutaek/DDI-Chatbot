from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    current_drugs: List[str] = Field(default_factory=list)
    age: int | None = None
    pregnant: bool = False
    liver_disease: bool = False
    kidney_disease: bool = False
    stomach_issue: bool = False


class DDIResult(BaseModel):
    drugs: List[str]
    severity: str
    summary: str
    recommendation: str
    source: str | None = None


class ChatResponse(BaseModel):
    user_message: str
    normalized_drugs: List[str] = Field(default_factory=list)
    extracted_drugs: List[str] = Field(default_factory=list)
    ddi_summary: str
    ddi_results: List[DDIResult] = Field(default_factory=list)
    answer: str
    personalized_warnings: List[str] = Field(default_factory=list)
    