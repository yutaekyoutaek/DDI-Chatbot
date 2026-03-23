import json
from typing import Any, Optional

from app.core.config import settings
from app.schemas.chat import DDIResult


class LLMService:
    def __init__(self):
        self.enabled = settings.use_llm and bool(settings.factchat_api_key)
        self.client: Optional[Any] = None

        print("[LLMService.__init__] USE_LLM =", settings.use_llm)
        print("[LLMService.__init__] FACTCHAT_API_KEY exists =", bool(settings.factchat_api_key))
        print("[LLMService.__init__] FACTCHAT_BASE_URL =", settings.factchat_base_url)
        print("[LLMService.__init__] FACTCHAT_MODEL =", settings.factchat_model)
        print("[LLMService.__init__] enabled =", self.enabled)

        if not self.enabled:
            print("[LLMService.__init__] LLM 비활성화 상태이므로 fallback만 사용합니다.")
            return

        try:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=settings.factchat_api_key,
                base_url=settings.factchat_base_url,
            )
            print("[LLMService.__init__] OpenAI client 초기화 성공")
        except Exception as e:
            print(f"[LLMService.__init__] OpenAI client 초기화 실패: {e}")
            self.client = None
            self.enabled = False

    def generate_explanation(
        self,
        user_message: str,
        normalized_drugs: list[str],
        ddi_results: list[DDIResult],
        personalized_warnings: list[str],
    ) -> Optional[str]:
        print("[LLMService.generate_explanation] called")
        print("[LLMService.generate_explanation] enabled =", self.enabled)
        print("[LLMService.generate_explanation] client exists =", self.client is not None)

        if not self.enabled or self.client is None:
            print("[LLMService.generate_explanation] LLM 사용 불가 -> fallback 반환 예정")
            return None

        ddi_payload = [
            {
                "drugs": item.drugs,
                "severity": item.severity,
                "summary": item.summary,
                "recommendation": item.recommendation,
            }
            for item in ddi_results
        ]

        system_prompt = (
            "너는 약물안전 설명 도우미다. "
            "반드시 제공된 구조화된 결과만 바탕으로 설명해야 한다. "
            "없는 의학적 사실을 추측하거나 새로운 상호작용, 새로운 위험도, 새로운 약물 판단을 만들어내면 안 된다. "
            "DDI 판단은 이미 끝난 상태이며, 너의 역할은 결과를 한국어로 쉽게 풀어서 설명하는 것이다. "
            "설명은 일반 사용자가 이해하기 쉬운 문장으로 작성하라. "
            "응답은 평문 문자열만 작성하라."
        )

        user_payload = {
            "user_message": user_message,
            "normalized_drugs": normalized_drugs,
            "ddi_results": ddi_payload,
            "personalized_warnings": personalized_warnings,
        }

        user_prompt = (
            "아래 구조화된 약물 점검 결과를 바탕으로, "
            "사용자에게 자연스럽고 이해하기 쉬운 최종 안내 문장을 작성해줘.\n\n"
            "조건:\n"
            "1. 가장 위험한 조합을 먼저 설명할 것\n"
            "2. 개인 맞춤 경고가 있으면 따로 언급할 것\n"
            "3. 새로운 의학 판단을 추가하지 말 것\n"
            "4. 마지막에 전문가 상담 권고를 짧게 덧붙일 것\n\n"
            f"{json.dumps(user_payload, ensure_ascii=False, indent=2)}"
        )

        try:
            print("[LLMService.generate_explanation] FactChat 호출 시도")

            response = self.client.chat.completions.create(
                model=settings.factchat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            print("[LLMService.generate_explanation] FactChat 응답 수신 성공")

            content = response.choices[0].message.content
            print("[LLMService.generate_explanation] content exists =", bool(content))

            if content:
                print("[LLMService.generate_explanation] LLM 답변 사용")
                return content.strip()

            print("[LLMService.generate_explanation] content 비어 있음 -> fallback")
            return None

        except Exception as e:
            print(f"[LLMService.generate_explanation] FactChat 호출 실패: {e}")
            return None

    def generate_answer(
        self,
        user_message: str,
        ddi_summary: str,
        ddi_results: list[dict],
        personalized_warnings: list[str],
        fallback_answer: str,
    ) -> str:
        try:
            explanation = self.generate_explanation(
                user_message=user_message,
                normalized_drugs=[],
                ddi_results=[
                    DDIResult(**item) if isinstance(item, dict) else item
                    for item in ddi_results
                ],
                personalized_warnings=personalized_warnings,
            )
            return explanation if explanation else fallback_answer
        except Exception:
            return fallback_answer