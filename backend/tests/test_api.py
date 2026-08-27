from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4

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


def test_wedding_invitation_apk_variations_are_phishing() -> None:
    messages = [
        "Halo kak, detail waktu dan lokasi ada di Undangan Pernikahan.apk. Ditunggu kehadirannya!",
        "Kepada Yth. Bapak/Ibu, kami lampirkan Undangan_Digital_Pernikahan.apk. Mohon diunduh untuk melihat peta lokasi.",
        "Kami mengundang Anda ke pesta pernikahan. Buka Foto Undangan.apk untuk info lengkapnya.",
    ]
    for message in messages:
        response = client.post("/api/analyze", json={"text": message})
        body = response.json()
        assert response.status_code == 200
        assert body["category"] == "Phishing/Link Berbahaya"
        assert body["risk_level"] == "HIGH"
        assert body["risk_score"] >= 0.7


def test_admin_dashboard_requires_key_and_supports_moderation(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-secret")
    assert client.get("/api/admin/dashboard").status_code == 401
    assert client.get("/api/admin/dashboard", headers={"X-API-Key": "wrong"}).status_code == 401

    created = client.post("/api/report", json={
        "text": "Undangan palsu untuk ditinjau admin",
        "category_suggested": "Phishing/Link Berbahaya",
        "consent": True,
    })
    headers = {"X-API-Key": "test-admin-secret"}
    dashboard = client.get("/api/admin/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["reports_pending"] >= 1
    assert dashboard.json()["database_connected"] is True
    assert dashboard.json()["database_engine"] in {"sqlite", "postgresql"}
    assert isinstance(dashboard.json()["daily_stats"], list)
    assert isinstance(dashboard.json()["source_counts"], dict)

    report_id = created.json()["id"]
    updated = client.patch(f"/api/admin/reports/{report_id}", headers=headers, json={"status": "reviewed"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "reviewed"


def test_user_registration_login_and_role_management(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-secret")
    email = f"user-{uuid4().hex[:8]}@example.com"
    registered = client.post("/api/auth/register", json={"name": "Pengguna Uji", "email": email, "password": "rahasia123"})
    assert registered.status_code == 201
    assert registered.json()["user"]["role"] == "user"
    assert "analyze" in registered.json()["user"]["permissions"]

    token = registered.json()["access_token"]
    profile = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == email

    headers = {"X-API-Key": "test-admin-secret"}
    users = client.get("/api/admin/users", headers=headers)
    target = next(item for item in users.json() if item["email"] == email)
    promoted = client.patch(f"/api/admin/users/{target['id']}", headers=headers, json={"role": "analyst"})
    assert promoted.status_code == 200
    assert "view_aggregate_stats" in promoted.json()["permissions"]

    login = client.post("/api/auth/login", json={"email": email, "password": "rahasia123"})
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "analyst"


def test_dynamic_education_and_anonymized_dataset(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-secret")
    headers = {"X-API-Key": "test-admin-secret"}
    education = client.post("/api/admin/education", headers=headers, json={
        "title": "Waspada Undangan APK",
        "category": "Phishing/Link Berbahaya",
        "description": "File undangan APK dapat memasang aplikasi berbahaya.",
        "warning_signs": ["Berkas berakhiran .apk"],
        "prevention": ["Jangan memasang APK dari pesan"],
        "is_published": True,
    })
    assert education.status_code == 201
    assert any(item["title"] == "Waspada Undangan APK" for item in client.get("/api/education").json())

    report = client.post("/api/report", json={
        "text": "Hubungi saya 081234567890 atau test@example.com, penipu kirim undangan.apk",
        "category_suggested": "Phishing/Link Berbahaya",
        "consent": True,
    }).json()
    assert client.patch(f"/api/admin/reports/{report['id']}", headers=headers, json={"status":"reviewed"}).status_code == 200
    processed = client.post(f"/api/admin/reports/{report['id']}/dataset", headers=headers)
    assert processed.status_code == 201
    assert "081234567890" not in processed.json()["text_anonymized"]
    assert "test@example.com" not in processed.json()["text_anonymized"]
    assert client.get("/api/dataset").status_code == 200

