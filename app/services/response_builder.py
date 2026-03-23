from __future__ import annotations

from typing import Callable, Dict, List, Optional


class ResponseBuilder:
    def __init__(self, display_name_getter: Optional[Callable[[str], str]] = None) -> None:
        self.display_name_getter = display_name_getter or (lambda x: x)

    def _to_display_name(self, drug_name: str) -> str:
        return self.display_name_getter(drug_name)

    def build_ddi_summary(self, ddi_results: List[Dict[str, object]]) -> str:
        if not ddi_results:
            return "현재 등록된 규칙 기준으로 확인된 상호작용은 없습니다."

        sorted_results = sorted(
            ddi_results,
            key=lambda x: self._severity_rank(str(x.get("severity", "low"))),
            reverse=True,
        )

        top = sorted_results[0]
        drugs = top.get("drugs", [])

        if isinstance(drugs, list) and len(drugs) == 2:
            drug_a = self._to_display_name(str(drugs[0]))
            drug_b = self._to_display_name(str(drugs[1]))
            severity = str(top.get("severity", "moderate"))
            return f"가장 주의가 필요한 조합은 {drug_a} + {drug_b} ({severity}) 입니다."

        return "약물 상호작용 가능성이 확인되었습니다."

    def build_answer(
        self,
        ddi_results: List[Dict[str, object]],
        ddi_summary: str,
        personalized_warnings: List[str],
    ) -> str:
        lines: List[str] = [ddi_summary]

        if ddi_results:
            lines.append("확인된 상호작용 정보:")
            for result in ddi_results:
                drugs = result.get("drugs", [])
                severity = str(result.get("severity", "moderate"))
                summary = str(result.get("summary", ""))
                recommendation = str(result.get("recommendation", ""))

                if isinstance(drugs, list) and len(drugs) == 2:
                    drug_a = self._to_display_name(str(drugs[0]))
                    drug_b = self._to_display_name(str(drugs[1]))
                    lines.append(f"- {drug_a} + {drug_b} [{severity}]")
                else:
                    lines.append(f"- 상호작용 [{severity}]")

                if summary:
                    lines.append(f"  - 요약: {summary}")
                if recommendation:
                    lines.append(f"  - 권장사항: {recommendation}")

        if personalized_warnings:
            lines.append("추가 주의사항:")
            for warning in personalized_warnings:
                lines.append(f"- {warning}")

        if not ddi_results and not personalized_warnings:
            lines.append(
                "이 결과는 MVP 단계의 규칙 기반 점검 결과이며, 실제 복용 전에는 의사 또는 약사와 상담하는 것이 가장 안전합니다."
            )
        else:
            lines.append("실제 복용 전에는 의사 또는 약사와 상담하는 것이 가장 안전합니다.")

        return "\n".join(lines)

    @staticmethod
    def _severity_rank(severity: str) -> int:
        order = {
            "high": 3,
            "moderate": 2,
            "low": 1,
        }
        return order.get(severity.lower(), 0)