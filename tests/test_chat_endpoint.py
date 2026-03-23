from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_endpoint_extracts_drugs_from_message():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "타이레놀이랑 이부프로펜 같이 먹어도 되나요?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "normalized_drugs" in data
    assert "extracted_drugs" in data
    assert "ddi_results" in data
    assert "answer" in data

    assert "acetaminophen" in data["normalized_drugs"]
    assert "ibuprofen" in data["normalized_drugs"]
    assert "acetaminophen" in data["extracted_drugs"]
    assert "ibuprofen" in data["extracted_drugs"]


def test_chat_endpoint_merges_current_drugs_and_message_drugs():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "애드빌도 같이 먹어도 되나요?",
            "current_drugs": ["타이레놀"]
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "acetaminophen" in data["normalized_drugs"]
    assert "ibuprofen" in data["normalized_drugs"]


def test_chat_endpoint_returns_ddi_result_for_known_pair():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "이부프로펜이랑 록소프로펜 같이 먹어도 돼?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["ddi_results"]) >= 1

    first = data["ddi_results"][0]
    assert "drugs" in first
    assert "severity" in first
    assert "summary" in first
    assert "recommendation" in first


def test_chat_endpoint_handles_no_drug_message():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "오늘 점심 뭐 먹지?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["normalized_drugs"] == []
    assert data["extracted_drugs"] == []
    assert isinstance(data["answer"], str)
    assert "ddi_results" in data


def test_chat_endpoint_includes_personalized_warning():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "아스피린 먹어도 되나요?",
            "pregnant": True
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "personalized_warnings" in data
    assert isinstance(data["personalized_warnings"], list)
    

def test_chat_endpoint_warfarin_ibuprofen_high_risk():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "와파린이랑 이부프로펜 같이 먹어도 되나요?"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["ddi_results"]) >= 1
    assert data["ddi_results"][0]["severity"] in ["high", "moderate"]
    
    
def test_chat_endpoint_detects_duplicate_ingredient_warning():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "타이레놀이랑 acetaminophen 같이 먹어도 되나요?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "personalized_warnings" in data
    assert any("중복 복용" in warning for warning in data["personalized_warnings"])
    
    
def test_chat_endpoint_duplicate_warning_uses_korean_display_name():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "타이레놀이랑 acetaminophen 같이 먹어도 되나요?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert any("아세트아미노펜" in warning for warning in data["personalized_warnings"])

def test_chat_endpoint_detects_duplicate_ingredient_warning(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "타이레놀이랑 acetaminophen 같이 먹어도 되나요?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "acetaminophen" in data["normalized_drugs"]
    assert data["extracted_drugs"] == ["acetaminophen", "acetaminophen"]
    assert any("중복 복용" in warning for warning in data["personalized_warnings"])
    
def test_chat_endpoint_extracts_compound_product(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "판콜에이 먹고 있는데 이부프로펜 추가로 먹어도 돼?"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "acetaminophen" in data["normalized_drugs"]
    assert "chlorpheniramine" in data["normalized_drugs"]
    assert "pseudoephedrine" in data["normalized_drugs"]
    assert "dextromethorphan" in data["normalized_drugs"]
    assert "ibuprofen" in data["normalized_drugs"]


def test_chat_endpoint_current_drugs_compound_expansion(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "이부프로펜 먹어도 돼?",
            "current_drugs": ["판콜에이"]
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "acetaminophen" in data["normalized_drugs"]
    assert "chlorpheniramine" in data["normalized_drugs"]
    assert "pseudoephedrine" in data["normalized_drugs"]
    assert "dextromethorphan" in data["normalized_drugs"]
    assert "ibuprofen" in data["normalized_drugs"]