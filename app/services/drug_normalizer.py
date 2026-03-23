from __future__ import annotations

from typing import List, Optional

from app.repositories.compound_product_repository import CompoundProductRepository
from app.repositories.drug_alias_repository import DrugAliasRepository


class DrugNormalizer:
    def __init__(
        self,
        alias_repository: Optional[DrugAliasRepository] = None,
        compound_product_repository: Optional[CompoundProductRepository] = None,
    ) -> None:
        self.alias_repository = alias_repository or DrugAliasRepository()
        self.compound_product_repository = compound_product_repository or CompoundProductRepository()

    def normalize(self, drug_name: str) -> Optional[str]:
        if not drug_name:
            return None

        normalized = self.alias_repository.normalize(drug_name)
        if normalized:
            return normalized

        lowered = drug_name.strip().lower()

        # 이미 영문 ingredient처럼 들어온 경우는 그대로 통과
        known_ingredient_like = {
            "acetaminophen",
            "ibuprofen",
            "warfarin",
            "aspirin",
            "naproxen",
            "dexibuprofen",
            "loxoprofen",
            "chlorpheniramine",
            "pseudoephedrine",
            "dextromethorphan",
        }
        if lowered in known_ingredient_like:
            return lowered

        return f"unknown:{drug_name.strip()}"

    def normalize_many(self, drug_names: List[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()

        for drug_name in drug_names:
            normalized_name = self.normalize(drug_name)
            if normalized_name and normalized_name not in seen:
                normalized.append(normalized_name)
                seen.add(normalized_name)

        return normalized

    def normalize_many_keep_duplicates(self, drug_names: List[str]) -> List[str]:
        normalized: List[str] = []

        for drug_name in drug_names:
            normalized_name = self.normalize(drug_name)
            if normalized_name:
                normalized.append(normalized_name)

        return normalized

    def extract_drugs_from_text(self, text: str) -> List[str]:
        """
        테스트 기준: 중복 제거 결과 반환
        """
        raw = self.extract_drugs_from_text_raw(text)
        return self.normalize_many(raw)

    def extract_drugs_from_text_raw(self, text: str) -> List[str]:
        """
        중복 유지 + 복합제 expand
        """
        if not text:
            return []

        lowered_text = text.lower()
        found: List[str] = []

        # 1) 복합제 먼저 추출 후 성분으로 확장
        for compound_alias in self.compound_product_repository.compound_map.keys():
            if compound_alias in lowered_text:
                ingredients = self.compound_product_repository.expand(compound_alias)
                found.extend(ingredients)

        # 2) 일반 alias 추출
        for alias in self.alias_repository.get_all_aliases():
            if alias.lower() in lowered_text:
                normalized_name = self.alias_repository.normalize(alias)
                if normalized_name:
                    found.append(normalized_name)

        return found

    def expand_compound_drugs(self, drug_names: List[str]) -> List[str]:
        expanded: List[str] = []

        for drug_name in drug_names:
            ingredients = self.compound_product_repository.expand(drug_name)
            if ingredients:
                expanded.extend(ingredients)
            else:
                expanded.append(drug_name)

        return expanded