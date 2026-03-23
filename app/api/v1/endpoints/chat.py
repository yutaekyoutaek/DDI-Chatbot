from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.repositories.compound_product_repository import CompoundProductRepository
from app.repositories.drug_alias_repository import DrugAliasRepository
from app.repositories.drug_display_repository import DrugDisplayRepository
from app.services.ddi_checker import DDIChecker
from app.services.drug_normalizer import DrugNormalizer
from app.services.llm_service import LLMService
from app.services.response_builder import ResponseBuilder
from app.services.risk_engine import RiskEngine

router = APIRouter()

alias_repository = DrugAliasRepository()
compound_product_repository = CompoundProductRepository()
drug_display_repository = DrugDisplayRepository()

drug_normalizer = DrugNormalizer(
    alias_repository=alias_repository,
    compound_product_repository=compound_product_repository,
)
ddi_checker = DDIChecker()
risk_engine = RiskEngine(display_name_getter=drug_display_repository.get_display_name)
response_builder = ResponseBuilder(display_name_getter=drug_display_repository.get_display_name)
llm_service = LLMService()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    current_drugs = request.current_drugs or []

    # 1) current_drugs 내 복합제 확장
    expanded_current_drugs = drug_normalizer.expand_compound_drugs(current_drugs)

    # 2) message에서 약물 추출 (중복 유지 / 복합제 expand 반영)
    extracted_drugs = drug_normalizer.extract_drugs_from_text_raw(request.message)

    # 3) current_drugs + extracted_drugs 합치기
    merged_raw_drugs = expanded_current_drugs + extracted_drugs

    # 4) raw / dedup 정규화 분리
    normalized_drugs_raw = drug_normalizer.normalize_many_keep_duplicates(merged_raw_drugs)
    normalized_drugs = drug_normalizer.normalize_many(merged_raw_drugs)

    # unknown:* 는 DDI pair 검사에서 제외
    known_normalized_drugs = [drug for drug in normalized_drugs if not drug.startswith("unknown:")]

    # 5) DDI 검사
    ddi_results = ddi_checker.check_many(known_normalized_drugs)

    # 6) 개인화/중복 성분 경고
    personalized_warnings = risk_engine.evaluate(
        normalized_drugs=normalized_drugs_raw,
        age=request.age,
        pregnant=request.pregnant,
        liver_disease=request.liver_disease,
        kidney_disease=request.kidney_disease,
        stomach_issue=request.stomach_issue,
    )

    # 7) 요약/답변 생성
    ddi_summary = response_builder.build_ddi_summary(ddi_results)
    fallback_answer = response_builder.build_answer(
        ddi_results=ddi_results,
        ddi_summary=ddi_summary,
        personalized_warnings=personalized_warnings,
    )

    answer = llm_service.generate_answer(
        user_message=request.message,
        ddi_summary=ddi_summary,
        ddi_results=ddi_results,
        personalized_warnings=personalized_warnings,
        fallback_answer=fallback_answer,
    )

    return ChatResponse(
        user_message=request.message,
        normalized_drugs=known_normalized_drugs,
        extracted_drugs=extracted_drugs,
        ddi_summary=ddi_summary,
        ddi_results=ddi_results,
        answer=answer,
        personalized_warnings=personalized_warnings,
    )