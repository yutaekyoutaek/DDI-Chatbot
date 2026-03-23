import json
from pathlib import Path


class DrugDisplayRepository:
    def __init__(self, display_file: str = "data/seeds/drug_display_names.json"):
        self.display_file = Path(display_file)
        self.display_map = self._load_display_map()

    def _load_display_map(self) -> dict[str, str]:
        if not self.display_file.exists():
            return {}

        with open(self.display_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            str(key).strip().lower(): str(value).strip()
            for key, value in data.items()
        }

    def get_display_name(self, ingredient: str) -> str:
        if not ingredient:
            return ""

        key = ingredient.strip().lower()
        return self.display_map.get(key, ingredient)