from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class DrugAliasRepository:
    def __init__(self) -> None:
        data_path = Path("data/seeds/drug_aliases.json")
        with data_path.open("r", encoding="utf-8") as f:
            rows = json.load(f)

        self.alias_to_ingredient: Dict[str, str] = {}
        self.aliases_in_order: List[str] = []

        for row in rows:
            alias = str(row.get("alias", "")).strip()
            ingredient = str(row.get("ingredient", "")).strip().lower()

            if not alias or not ingredient:
                continue

            key = alias.lower()
            self.alias_to_ingredient[key] = ingredient
            self.aliases_in_order.append(alias)

        # 긴 alias를 먼저 찾게 해서 부분 일치 충돌을 줄임
        self.aliases_in_order = sorted(
            set(self.aliases_in_order),
            key=lambda x: len(x),
            reverse=True,
        )

    def normalize(self, drug_name: str) -> Optional[str]:
        if not drug_name:
            return None
        return self.alias_to_ingredient.get(drug_name.strip().lower())

    def get_all_aliases(self) -> List[str]:
        return list(self.aliases_in_order)