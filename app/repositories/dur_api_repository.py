from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from app.repositories.base_ddi_repository import BaseDDIRepository
from app.repositories.drug_display_repository import DrugDisplayRepository


class DURApiRepository(BaseDDIRepository):
    """
    식약처 DUR OpenAPI 연동 repository

    현재 Swagger 기준:
    - operation: getUsjntTabooInfoList02
    - 단일 성분 조회형 API
    - ingrKorName 또는 ingrCode 로 조회
    - 응답의 MIXTURE_INGR_KOR_NAME 에서 상대 성분을 찾아 pair 매칭

    동작 원칙:
    - 프로젝트 내부 normalized 성분명은 영문 기준일 수 있음
      예: ibuprofen, loxoprofen
    - DUR API는 ingrKorName(한글 성분명) 기준 조회가 더 잘 맞음
    - 따라서 조회 직전에 영문 성분명을 display name(한글)로 변환해서 사용
    - API 실패/미매칭 시 None 반환 -> 상위 hybrid에서 seed fallback
    """

    def __init__(self) -> None:
        self.service_key = os.getenv("DUR_API_SERVICE_KEY", "").strip()
        self.base_url = os.getenv("DUR_API_BASE_URL", "").strip()
        self.operation = os.getenv("DUR_API_OPERATION", "").strip()
        self.timeout = int(os.getenv("DUR_API_TIMEOUT", "5"))

        # request params
        self.service_key_param = os.getenv("DUR_API_SERVICE_KEY_PARAM", "serviceKey").strip() or "serviceKey"
        self.page_no_param = os.getenv("DUR_API_PAGE_NO_PARAM", "pageNo").strip() or "pageNo"
        self.num_of_rows_param = os.getenv("DUR_API_NUM_OF_ROWS_PARAM", "numOfRows").strip() or "numOfRows"
        self.type_param = os.getenv("DUR_API_TYPE_PARAM", "type").strip() or "type"
        self.type_name_param = os.getenv("DUR_API_TYPE_NAME_PARAM", "typeName").strip() or "typeName"
        self.ingredient_code_param = os.getenv("DUR_API_INGREDIENT_CODE_PARAM", "ingrCode").strip() or "ingrCode"
        self.ingredient_name_param = os.getenv("DUR_API_INGREDIENT_NAME_PARAM", "ingrKorName").strip() or "ingrKorName"
        self.response_format = os.getenv("DUR_API_RESPONSE_FORMAT", "json").strip() or "json"

        # response fields
        self.response_type_name_field = os.getenv("DUR_API_RESPONSE_TYPE_NAME_FIELD", "TYPE_NAME").strip() or "TYPE_NAME"
        self.response_ingredient_code_field = (
            os.getenv("DUR_API_RESPONSE_INGREDIENT_CODE_FIELD", "INGR_CODE").strip() or "INGR_CODE"
        )
        self.response_ingredient_name_field = (
            os.getenv("DUR_API_RESPONSE_INGREDIENT_NAME_FIELD", "INGR_KOR_NAME").strip() or "INGR_KOR_NAME"
        )
        self.response_mixture_ingredient_code_field = (
            os.getenv("DUR_API_RESPONSE_MIXTURE_INGREDIENT_CODE_FIELD", "MIXTURE_INGR_CODE").strip()
            or "MIXTURE_INGR_CODE"
        )
        self.response_mixture_ingredient_name_field = (
            os.getenv("DUR_API_RESPONSE_MIXTURE_INGREDIENT_NAME_FIELD", "MIXTURE_INGR_KOR_NAME").strip()
            or "MIXTURE_INGR_KOR_NAME"
        )
        self.response_summary_field = (
            os.getenv("DUR_API_RESPONSE_SUMMARY_FIELD", "PROHBT_CONTENT").strip() or "PROHBT_CONTENT"
        )
        self.response_remark_field = os.getenv("DUR_API_RESPONSE_REMARK_FIELD", "REMARK").strip() or "REMARK"

        self.enabled = bool(self.service_key and self.base_url and self.operation)

        # 기존 프로젝트 seed display name 활용
        # 예: ibuprofen -> 이부프로펜
        self.display_repo = DrugDisplayRepository()

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[Dict[str, object]]:
        if not self.enabled:
            return None

        drug_a = drug_a.strip().lower()
        drug_b = drug_b.strip().lower()

        if not drug_a or not drug_b:
            return None

        try:
            drug_a_query_name = self._to_dur_query_name(drug_a)
            drug_b_query_name = self._to_dur_query_name(drug_b)

            # 1) drug_a 기준 조회 후 drug_b 매칭
            items_a = self._fetch_by_ingredient_name(drug_a_query_name)
            matched = self._find_matching_item(
                items_a,
                source_drug_query_name=drug_a_query_name,
                target_drug_query_name=drug_b_query_name,
            )
            if matched:
                return self._normalize_dur_item(
                    matched,
                    requested_drug_a=drug_a,
                    requested_drug_b=drug_b,
                )

            # 2) 반대 방향 조회
            items_b = self._fetch_by_ingredient_name(drug_b_query_name)
            matched = self._find_matching_item(
                items_b,
                source_drug_query_name=drug_b_query_name,
                target_drug_query_name=drug_a_query_name,
            )
            if matched:
                return self._normalize_dur_item(
                    matched,
                    requested_drug_a=drug_a,
                    requested_drug_b=drug_b,
                )

            return None

        except Exception:
            # API 실패 시 상위에서 seed fallback 가능하도록 None 반환
            return None

    def _to_dur_query_name(self, normalized_name: str) -> str:
        """
        프로젝트 내부 normalized 영문명을 DUR 조회용 한글명으로 변환
        예:
        - ibuprofen -> 이부프로펜
        - loxoprofen -> 록소프로펜

        display name이 한글이 아닐 수도 있으므로,
        값이 없으면 원래 normalized 이름을 그대로 사용한다.
        """
        if not normalized_name:
            return normalized_name

        display_name = self.display_repo.get_display_name(normalized_name)
        if display_name:
            return display_name.strip()

        return normalized_name.strip()

    def _fetch_by_ingredient_name(self, ingredient_name: str) -> List[Dict[str, object]]:
        url = self._build_url(ingredient_name=ingredient_name)

        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")

        data = json.loads(raw)
        return self._extract_items(data)

    def _build_url(self, ingredient_name: str) -> str:
        query = {
            self.service_key_param: self.service_key,
            self.page_no_param: "1",
            self.num_of_rows_param: "100",
            self.type_param: self.response_format,
            self.ingredient_name_param: ingredient_name,
        }

        query_string = urllib.parse.urlencode(query, doseq=True)
        return f"{self.base_url.rstrip('/')}/{self.operation.lstrip('/')}?{query_string}"

    def _extract_items(self, data: Dict[str, object]) -> List[Dict[str, object]]:
        if not isinstance(data, dict):
            return []

        # 현재 Swagger Example Value 기준: header/body 구조
        header = data.get("header")
        if isinstance(header, dict):
            result_code = str(header.get("resultCode", "")).strip()
            if result_code and result_code not in {"00", "0", "INFO-000"}:
                return []

        body = data.get("body")
        if isinstance(body, dict):
            items = body.get("items")
            if isinstance(items, dict):
                item = items.get("item")
                if isinstance(item, list):
                    return [x for x in item if isinstance(x, dict)]
                if isinstance(item, dict):
                    return [item]

        # 혹시 공공데이터포털 response.body 구조로 오는 경우도 방어
        response = data.get("response")
        if isinstance(response, dict):
            header = response.get("header")
            if isinstance(header, dict):
                result_code = str(header.get("resultCode", "")).strip()
                if result_code and result_code not in {"00", "0", "INFO-000"}:
                    return []

            body = response.get("body")
            if isinstance(body, dict):
                items = body.get("items")
                if isinstance(items, dict):
                    item = items.get("item")
                    if isinstance(item, list):
                        return [x for x in item if isinstance(x, dict)]
                    if isinstance(item, dict):
                        return [item]

        return []

    def _find_matching_item(
        self,
        items: List[Dict[str, object]],
        source_drug_query_name: str,
        target_drug_query_name: str,
    ) -> Optional[Dict[str, object]]:
        source_drug_query_name = source_drug_query_name.strip().lower()
        target_drug_query_name = target_drug_query_name.strip().lower()

        for item in items:
            ingr_name = str(item.get(self.response_ingredient_name_field, "")).strip().lower()
            mixture_name = str(item.get(self.response_mixture_ingredient_name_field, "")).strip().lower()

            # source 성분 기준으로 조회한 결과인지 확인
            if ingr_name and ingr_name != source_drug_query_name:
                continue

            if mixture_name == target_drug_query_name:
                return item

        return None

    def _normalize_dur_item(
        self,
        item: Dict[str, object],
        requested_drug_a: str,
        requested_drug_b: str,
    ) -> Dict[str, object]:
        summary = self._pick_first(
            item,
            [self.response_summary_field, "PROHBT_CONTENT"],
            default="DUR API에서 병용금기 정보가 확인되었습니다.",
        )

        recommendation = self._pick_first(
            item,
            [self.response_remark_field, "REMARK"],
            default="병용 전 의사 또는 약사와 상담하는 것이 안전합니다.",
        )

        return {
            "drugs": sorted([requested_drug_a.strip().lower(), requested_drug_b.strip().lower()]),
            "severity": "high",  # 병용금기 API이므로 high 고정
            "summary": str(summary).strip(),
            "recommendation": str(recommendation).strip(),
            "source": "dur_api",
            "raw": item,
        }

    @staticmethod
    def _pick_first(item: Dict[str, object], keys: List[str], default: str = "") -> str:
        for key in keys:
            value = item.get(key)
            if value not in (None, "", []):
                return str(value)
        return default