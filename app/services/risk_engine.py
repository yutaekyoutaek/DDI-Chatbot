from __future__ import annotations

from collections import Counter
from typing import Callable, List, Optional


class RiskEngine:
    def __init__(self, display_name_getter: Optional[Callable[[str], str]] = None) -> None:
        self.display_name_getter = display_name_getter or (lambda x: x)

    def _to_display_name(self, drug_name: str) -> str:
        return self.display_name_getter(drug_name)

    def evaluate(
        self,
        normalized_drugs: List[str],
        age: int | None = None,
        pregnant: bool = False,
        liver_disease: bool = False,
        kidney_disease: bool = False,
        stomach_issue: bool = False,
    ) -> List[str]:
        warnings: List[str] = []

        warnings.extend(self._check_duplicate_ingredients(normalized_drugs))

        if pregnant:
            warnings.append("임신 중이거나 임신 가능성이 있다면 복용 전 반드시 의사 또는 약사와 상담하세요.")

        if liver_disease:
            warnings.append("간 질환이 있다면 약물 용량이나 성분에 주의가 필요할 수 있습니다.")

        if kidney_disease:
            warnings.append("신장 질환이 있다면 약물 배설에 영향을 줄 수 있어 주의가 필요합니다.")

        if stomach_issue:
            nsaids = {"ibuprofen", "naproxen", "dexibuprofen", "loxoprofen"}
            taken_nsaids = [drug for drug in normalized_drugs if drug in nsaids]
            if taken_nsaids:
                display_names = [self._to_display_name(drug) for drug in sorted(set(taken_nsaids))]
                joined = ", ".join(display_names)
                warnings.append(f"위장 질환이 있다면 {joined} 같은 소염진통제 복용 시 위장관 부작용에 주의하세요.")

        if age is not None and age >= 65:
            warnings.append("고령자는 약물 부작용 위험이 더 클 수 있으므로 복용 전 전문가와 상담하는 것이 좋습니다.")

        return warnings

    def _check_duplicate_ingredients(self, normalized_drugs: List[str]) -> List[str]:
        warnings: List[str] = []
        counter = Counter(normalized_drugs)

        for drug_name, count in counter.items():
            if count >= 2:
                display_name = self._to_display_name(drug_name)
                warnings.append(
                    f"{display_name} 성분이 중복으로 포함되어 있을 수 있습니다. 동일 성분의 중복 복용에 주의하세요."
                )

        return warnings