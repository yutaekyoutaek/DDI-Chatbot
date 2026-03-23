from typing import Optional

from app.repositories.base_ddi_repository import BaseDDIRepository


class DURRepository(BaseDDIRepository):
    """
    식약처 DUR / 심평원 / 약학정보원 / 내부 DUR DB 등
    외부 데이터 소스 연동용 repository 뼈대.

    현재는 실제 API 호출 없이 interface만 제공한다.
    추후 _fetch_from_external_source() 내부를 구현하면 된다.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[dict]:
        if not self.enabled:
            return None

        return self._fetch_from_external_source(drug_a, drug_b)

    def _fetch_from_external_source(self, drug_a: str, drug_b: str) -> Optional[dict]:
        """
        TODO:
        - 실제 DUR/OpenAPI/내부DB 조회 구현
        - 반환 형식은 seed repository와 동일하게 맞춘다.

        예시 반환 형식:
        {
            "drugs": ["ibuprofen", "loxoprofen"],
            "severity": "moderate",
            "summary": "NSAID 계열 중복 복용으로 위장관 부작용 위험이 증가할 수 있습니다.",
            "recommendation": "가능하면 병용을 피하고, 필요 시 전문가와 상담하세요.",
            "source": "dur"
        }
        """
        return None