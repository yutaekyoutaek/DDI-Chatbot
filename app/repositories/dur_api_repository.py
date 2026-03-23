from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from app.repositories.base_ddi_repository import BaseDDIRepository


class DURApiRepository(BaseDDIRepository):
    """
    식약처 DUR OpenAPI 연동용 repository

    주의:
    - 실제 endpoint URL / query param / response field는
      data.go.kr에서 승인받은 API 문서 기준으로 최종 확인 필요
    - 이 코드는 '바로 붙여 넣어 확장 가능한 안전한 뼈대'다.
    """

    def __init__(self) -> None:
        self.service_key = os.getenv("DUR_API_SERVICE_KEY", "").strip()
        self.base_url = os.getenv("DUR_API_BASE_URL", "").strip()

        # 예:
        # DUR_API_OPERATION=UsjntTabooInfoService/getUsjntTabooInfoList
        # 또는 실제 승인받은 operation 경로
        self.operation = os.getenv("DUR_API_OPERATION", "").strip()

        self.timeout = int(os.getenv("DUR_API_TIMEOUT", "5"))
        self.enabled = bool(self.service_key and self.base_url and self.operation)

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[Dict[str, object]]:
        if not self.enabled:
            return None

        try:
            items = self._fetch_pair(drug_a, drug_b)

            if not items:
                items = self._fetch_pair(drug_b, drug_a)

            if not items:
                return None

            item = items[0]
            return self._normalize_dur_item(item, drug_a, drug_b)

        except Exception:
            # API 실패 시 상위에서 seed fallback 하도록 None 반환
            return None

    def _fetch_pair(self, drug_a: str, drug_b: str) -> List[Dict]:
        """
        실제 DUR API 스펙에 맞춰 query parameter를 수정하면 된다.
        현재는 가장 흔한 공공데이터 포털 패턴 기준의 뼈대.
        """
        url = self._build_url(drug_a, drug_b)

        with urllib.request.urlopen(url, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")

        data = json.loads(raw)
        return self._extract_items(data)

    def _build_url(self, drug_a: str, drug_b: str) -> str:
        # 실제 API 문서에 맞춰 키 이름 조정 필요
        query = {
            "serviceKey": self.service_key,
            "pageNo": "1",
            "numOfRows": "10",
            "type": "json",
            "itemNameA": drug_a,
            "itemNameB": drug_b,
        }

        query_string = urllib.parse.urlencode(query, doseq=True)
        return f"{self.base_url.rstrip('/')}/{self.operation.lstrip('/')}?{query_string}"

    def _extract_items(self, data: Dict) -> List[Dict]:
        """
        공공데이터 포털 응답 포맷 편차를 흡수
        """
        if not isinstance(data, dict):
            return []

        # 케이스 1: response.body.items.item
        response = data.get("response")
        if isinstance(response, dict):
            body = response.get("body")
            if isinstance(body, dict):
                items = body.get("items")
                if isinstance(items, dict):
                    item = items.get("item")
                    if isinstance(item, list):
                        return item
                    if isinstance(item, dict):
                        return [item]

        # 케이스 2: items 바로 존재
        items = data.get("items")
        if isinstance(items, list):
            return items
        if isinstance(items, dict):
            item = items.get("item")
            if isinstance(item, list):
                return item
            if isinstance(item, dict):
                return [item]

        # 케이스 3: data 리스트 바로 반환
        if isinstance(data.get("data"), list):
            return data["data"]

        return []

    def _normalize_dur_item(
        self,
        item: Dict,
        requested_drug_a: str,
        requested_drug_b: str,
    ) -> Dict[str, object]:
        """
        API 응답 필드를 현재 프로젝트의 ddi_rules.json 포맷과 맞춘다.
        실제 필드명은 승인받은 API 문서에 맞춰 추가 보정하면 된다.
        """

        severity = self._pick_first(
            item,
            [
                "severity",
                "SEVERITY",
                "prohbtLevel",
                "PROHBT_LEVEL",
                "typeName",
                "TYPE_NAME",
            ],
            default="moderate",
        )

        summary = self._pick_first(
            item,
            [
                "summary",
                "SUMMARY",
                "reason",
                "REASON",
                "prohbtContent",
                "PROHBT_CONTENT",
                "intrcInfo",
                "INTRC_INFO",
            ],
            default="DUR API에서 병용 주의 정보가 확인되었습니다.",
        )

        recommendation = self._pick_first(
            item,
            [
                "recommendation",
                "RECOMMENDATION",
                "action",
                "ACTION",
                "remark",
                "REMARK",
            ],
            default="복용 전 의사 또는 약사와 상담하는 것이 안전합니다.",
        )

        drug_a = self._pick_first(
            item,
            ["drugA", "DRUG_A", "itemNameA", "ITEM_NAME_A"],
            default=requested_drug_a,
        )
        drug_b = self._pick_first(
            item,
            ["drugB", "DRUG_B", "itemNameB", "ITEM_NAME_B"],
            default=requested_drug_b,
        )

        return {
            "drugs": sorted([str(drug_a).lower(), str(drug_b).lower()]),
            "severity": self._normalize_severity(str(severity)),
            "summary": str(summary),
            "recommendation": str(recommendation),
            "source": "dur_api",
            "raw": item,
        }

    @staticmethod
    def _pick_first(item: Dict, keys: List[str], default: str = "") -> str:
        for key in keys:
            value = item.get(key)
            if value not in (None, "", []):
                return str(value)
        return default

    @staticmethod
    def _normalize_severity(value: str) -> str:
        text = value.strip().lower()

        mapping = {
            "high": "high",
            "major": "high",
            "contraindicated": "high",
            "금기": "high",
            "병용금기": "high",
            "moderate": "moderate",
            "medium": "moderate",
            "주의": "moderate",
            "low": "low",
            "minor": "low",
        }

        return mapping.get(text, "moderate")