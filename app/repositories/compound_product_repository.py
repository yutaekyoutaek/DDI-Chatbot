from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class CompoundProductRepository:
    def __init__(self) -> None:
        data_path = Path("data/seeds/compound_products.json")
        with data_path.open("r", encoding="utf-8") as f:
            rows = json.load(f)

        self.compound_map: Dict[str, List[str]] = {}

        for row in rows:
            alias = str(row.get("alias", "")).strip().lower()
            ingredients = row.get("ingredients", [])

            if not alias or not isinstance(ingredients, list):
                continue

            self.compound_map[alias] = [str(x).strip().lower() for x in ingredients if str(x).strip()]

    def expand(self, drug_name: str) -> List[str]:
        if not drug_name:
            return []
        return list(self.compound_map.get(drug_name.strip().lower(), []))

    def is_compound_product(self, drug_name: str) -> bool:
        if not drug_name:
            return False
        return drug_name.strip().lower() in self.compound_map