from __future__ import annotations

import itertools
import os
from typing import Dict, List, Optional

from app.repositories.base_ddi_repository import BaseDDIRepository
from app.repositories.ddi_rule_repository import DDIRuleRepository
from app.repositories.dur_api_repository import DURApiRepository


class HybridDDIRepository(BaseDDIRepository):
    """
    API 우선, 실패/미존재 시 seed fallback
    """

    def __init__(
        self,
        primary_repo: BaseDDIRepository,
        fallback_repo: BaseDDIRepository,
    ) -> None:
        self.primary_repo = primary_repo
        self.fallback_repo = fallback_repo

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[Dict[str, object]]:
        primary_result = self.primary_repo.get_interaction(drug_a, drug_b)
        if primary_result:
            primary_result = dict(primary_result)
            primary_result.setdefault("source", "dur_api")
            return primary_result

        fallback_result = self.fallback_repo.get_interaction(drug_a, drug_b)
        if fallback_result:
            fallback_result = dict(fallback_result)
            fallback_result.setdefault("source", "seed")
            return fallback_result

        return None


def build_ddi_repository() -> BaseDDIRepository:
    """
    환경변수:
    - DDI_DATA_SOURCE=seed|dur|hybrid
    """

    source = os.getenv("DDI_DATA_SOURCE", "seed").strip().lower()

    seed_repo = DDIRuleRepository()
    dur_repo = DURApiRepository()

    if source == "dur":
        return dur_repo

    if source == "hybrid":
        return HybridDDIRepository(primary_repo=dur_repo, fallback_repo=seed_repo)

    return seed_repo


class DDIChecker:
    def __init__(self, ddi_repository: Optional[BaseDDIRepository] = None) -> None:
        self.ddi_repository = ddi_repository or build_ddi_repository()

    def check_pair(self, drug_a: str, drug_b: str) -> Optional[Dict[str, object]]:
        return self.ddi_repository.get_interaction(drug_a, drug_b)

    def check_many(self, normalized_drugs: List[str]) -> List[Dict[str, object]]:
        """
        normalized_drugs는 deduplicated 리스트라고 가정
        unknown:* 는 pairwise DDI 검사에서 제외
        """
        if not normalized_drugs or len(normalized_drugs) < 2:
            return []

        known_normalized_drugs = [
            drug.strip().lower()
            for drug in normalized_drugs
            if drug and not drug.startswith("unknown:")
        ]

        if len(known_normalized_drugs) < 2:
            return []

        pairs = list(itertools.combinations(sorted(set(known_normalized_drugs)), 2))
        return self.ddi_repository.get_interactions_for_pairs(pairs)