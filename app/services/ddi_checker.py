from __future__ import annotations

import itertools
import os
from typing import Dict, List, Optional

from app.repositories.base_ddi_repository import BaseDDIRepository
from app.repositories.dur_api_repository import DURApiRepository
from app.repositories.ddi_rule_repository import DDIRuleRepository

class DDIChecker:
    def __init__(self, repository: BaseDDIRepository | None = None):
        self.repository = repository or DDIRuleRepository()

    def check_pair(self, drug_a: str, drug_b: str) -> Optional[dict]:
        return self.repository.get_interaction(drug_a, drug_b)

    def check_many(self, drugs: list[str]) -> list[dict]:
        results: list[dict] = []
        seen_pairs: set[tuple[str, str]] = set()

        known_drugs = [
            drug.strip().lower()
            for drug in drugs
            if drug and not drug.startswith("unknown:")
        ]

        for drug_a, drug_b in combinations(known_drugs, 2):
            key = tuple(sorted([drug_a, drug_b]))
            if key in seen_pairs:
                continue

            seen_pairs.add(key)
            result = self.check_pair(drug_a, drug_b)

            if result:
                results.append(result)

        return results
    
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
        result = self.primary_repo.get_interaction(drug_a, drug_b)
        if result:
            return result

        result = self.fallback_repo.get_interaction(drug_a, drug_b)
        if result:
            result = dict(result)
            result.setdefault("source", "seed")
            return result

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

    def check_many(self, normalized_drugs: List[str]) -> List[Dict[str, object]]:
        """
        normalized_drugs는 deduplicated 리스트라고 가정
        """
        if not normalized_drugs or len(normalized_drugs) < 2:
            return []

        pairs = list(itertools.combinations(sorted(set(normalized_drugs)), 2))
        return self.ddi_repository.get_interactions_for_pairs(pairs)