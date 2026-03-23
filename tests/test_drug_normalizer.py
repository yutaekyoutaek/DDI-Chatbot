from app.services.drug_normalizer import DrugNormalizer


def test_normalize_known_drug():
    normalizer = DrugNormalizer()
    result = normalizer.normalize("타이레놀")
    assert result == "acetaminophen"


def test_normalize_unknown_drug():
    normalizer = DrugNormalizer()
    result = normalizer.normalize("이상한약")
    assert result.startswith("unknown:")


def test_normalize_many_removes_duplicates():
    normalizer = DrugNormalizer()
    result = normalizer.normalize_many(["타이레놀", "acetaminophen", "타이레놀"])
    assert result == ["acetaminophen"]


def test_extract_drugs_from_text_basic():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("타이레놀이랑 이부프로펜 같이 먹어도 되나요?")
    assert "acetaminophen" in result
    assert "ibuprofen" in result
    assert len(result) == 2


def test_extract_drugs_from_text_with_brand_names():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("애드빌 먹고 있는데 록소닌도 같이 먹어도 돼?")
    assert "ibuprofen" in result
    assert "loxoprofen" in result


def test_extract_drugs_from_text_deduplicates_same_ingredient():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("타이레놀하고 acetaminophen 같이 적으면 하나로 봐야 해")
    assert result == ["acetaminophen"]


def test_extract_drugs_from_text_empty():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("")
    assert result == []


def test_extract_drugs_from_text_no_match():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("오늘 점심 뭐 먹지?")
    assert result == []
    
def test_extract_naproxen_from_brand_name():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("낙센 먹고 있어")
    assert "naproxen" in result


def test_extract_aspirin():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("아스피린 먹었어")
    assert "aspirin" in result
    
def test_normalize_many_keep_duplicates():
    normalizer = DrugNormalizer()
    result = normalizer.normalize_many_keep_duplicates(
        ["타이레놀", "acetaminophen", "애드빌"]
    )
    assert result == ["acetaminophen", "acetaminophen", "ibuprofen"]
    
def test_extract_drugs_from_text_deduplicates_same_ingredient():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("타이레놀하고 acetaminophen 같이 적으면 하나로 봐야 해")
    assert result == ["acetaminophen"]
    
def test_extract_compound_product_from_text():
    normalizer = DrugNormalizer()
    result = normalizer.extract_drugs_from_text("판콜에이 먹고 있어")
    assert "acetaminophen" in result
    assert "chlorpheniramine" in result
    assert "pseudoephedrine" in result
    assert "dextromethorphan" in result


def test_expand_compound_drugs_from_current_drugs():
    normalizer = DrugNormalizer()
    result = normalizer.expand_compound_drugs(["판콜에이", "타이레놀"])
    assert "acetaminophen" in result
    assert "chlorpheniramine" in result
    assert "pseudoephedrine" in result
    assert "dextromethorphan" in result
    assert "타이레놀" in result