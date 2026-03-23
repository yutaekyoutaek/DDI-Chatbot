import json
from pathlib import Path
from typing import Optional

from app.repositories.base_ddi_repository import BaseDDIRepository


class DDIRuleRepository(BaseDDIRepository):
    def __init__(self, rules_file: str = "data/seeds/ddi_rules.json"):
        self.rules_file = Path(rules_file)
        self.rule_map = self._load_rule_map()

    def _load_rule_map(self) -> dict[tuple[str, str], dict]:
        if not self.rules_file.exists():
            return {}

        with open(self.rules_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        rule_map: dict[tuple[str, str], dict] = {}

        for item in data:
            drugs = item.get("drugs", [])
            if len(drugs) != 2:
                continue

            a, b = sorted([drugs[0].strip().lower(), drugs[1].strip().lower()])

            rule_map[(a, b)] = {
                "drugs": [a, b],
                "severity": item.get("severity", "unknown"),
                "summary": item.get("summary", ""),
                "recommendation": item.get("recommendation", ""),
                "source": "seed",
            }

        return rule_map

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[dict]:
        key = tuple(sorted([drug_a.strip().lower(), drug_b.strip().lower()]))
        return self.rule_map.get(key)