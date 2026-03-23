from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


DDIRule = Dict[str, object]


class BaseDDIRepository(ABC):
    """
    DDI 조회 소스 공통 인터페이스
    - seed json
    - DUR API
    - 향후 약학정보원/내부 DB
    모두 이 인터페이스를 따르게 한다.
    """

    @abstractmethod
    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[DDIRule]:
        raise NotImplementedError

    def get_interactions_for_pairs(self, pairs: List[tuple[str, str]]) -> List[DDIRule]:
        results: List[DDIRule] = []
        for drug_a, drug_b in pairs:
            rule = self.get_interaction(drug_a, drug_b)
            if rule:
                results.append(rule)
        return results