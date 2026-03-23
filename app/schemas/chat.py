#채팅 요청/응답 형식을 정의하는 파일
from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자가 입력한 질문")
    age: Optional[int] = Field(None, description="사용자 나이")
    pregnant: Optional[bool] = Field(None, description="임신 여부")
    liver_disease: Optional[bool] = Field(None, description="간 질환 여부")
    kidney_disease: Optional[bool] = Field(None, description="신장 질환 여부")
    stomach_issue: Optional[bool] = Field(None, description="위장 질환 또는 속쓰림 여부")
    current_drugs: Optional[List[str]] = Field(default_factory=list, description="현재 복용 중인 약 목록")


class DDIResult(BaseModel):
    drugs: List[str]
    severity: str
    summary: str
    recommendation: str


class ChatResponse(BaseModel):
    user_message: str
    normalized_drugs: List[str]
    extracted_drugs: List[str] = []
    ddi_summary: str
    ddi_results: List[DDIResult]
    answer: str
    personalized_warnings: List[str]