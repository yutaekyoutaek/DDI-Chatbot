from app.services.ddi_checker import DDIChecker, HybridDDIRepository


class FakePrimaryRepo:
    def __init__(self, result=None):
        self.result = result

    def get_interaction(self, drug_a, drug_b):
        return self.result

    def get_interactions_for_pairs(self, pairs):
        results = []
        for a, b in pairs:
            r = self.get_interaction(a, b)
            if r:
                results.append(r)
        return results


class FakeFallbackRepo(FakePrimaryRepo):
    pass


def test_hybrid_repository_uses_primary_first():
    primary = FakePrimaryRepo(
        {
            "drugs": ["ibuprofen", "warfarin"],
            "severity": "high",
            "summary": "api result",
            "recommendation": "avoid",
            "source": "dur_api",
        }
    )
    fallback = FakeFallbackRepo(
        {
            "drugs": ["ibuprofen", "warfarin"],
            "severity": "high",
            "summary": "seed result",
            "recommendation": "avoid",
            "source": "seed",
        }
    )

    repo = HybridDDIRepository(primary_repo=primary, fallback_repo=fallback)
    result = repo.get_interaction("warfarin", "ibuprofen")

    assert result is not None
    assert result["source"] == "dur_api"
    assert result["summary"] == "api result"


def test_hybrid_repository_falls_back_to_seed():
    primary = FakePrimaryRepo(result=None)
    fallback = FakeFallbackRepo(
        {
            "drugs": ["ibuprofen", "warfarin"],
            "severity": "high",
            "summary": "seed result",
            "recommendation": "avoid",
            "source": "seed",
        }
    )

    repo = HybridDDIRepository(primary_repo=primary, fallback_repo=fallback)
    result = repo.get_interaction("warfarin", "ibuprofen")

    assert result is not None
    assert result["source"] == "seed"


def test_ddi_checker_checks_all_pairs():
    class FakeRepo:
        def get_interaction(self, drug_a, drug_b):
            key = tuple(sorted([drug_a, drug_b]))
            if key == ("ibuprofen", "warfarin"):
                return {
                    "drugs": ["ibuprofen", "warfarin"],
                    "severity": "high",
                    "summary": "found",
                    "recommendation": "avoid",
                    "source": "seed",
                }
            return None

        def get_interactions_for_pairs(self, pairs):
            results = []
            for a, b in pairs:
                r = self.get_interaction(a, b)
                if r:
                    results.append(r)
            return results

    checker = DDIChecker(ddi_repository=FakeRepo())
    results = checker.check_many(["warfarin", "ibuprofen", "acetaminophen"])

    assert len(results) == 1
    assert results[0]["severity"] == "high"