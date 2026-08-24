from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_is_ephemeral_and_returns_complete_contract() -> None:
    response = client.post("/api/analyze", json={"text": "Segera kirim OTP atau akun diblokir", "source": "test"})
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "HIGH"
    assert len(body["nseae_scores"]) == 6
    assert body["recommendation"]
    assert body["model_source"] in {"indobert", "rules-fallback"}

def test_report_requires_explicit_consent() -> None:
    response = client.post("/api/report", json={"text": "contoh", "category_suggested": "Social Engineering", "consent": False})
    assert response.status_code == 400

def test_public_content_endpoints() -> None:
    assert len(client.get("/api/categories").json()) == 5
    assert client.get("/api/stats").status_code == 200
