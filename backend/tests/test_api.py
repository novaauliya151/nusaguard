from fastapi.testclient import TestClient
from app.main import app
from app.services.store import store
from uuid import uuid4

client = TestClient(app)

def auth_headers(role: str = "admin") -> dict[str, str]:
    email = f"{role}-{uuid4().hex[:10]}@example.com"
    user = store.create_user(f"Akun {role}", email, "rahasia123", role)
    assert user is not None
    result = store.authenticate(email, "rahasia123")
    assert result is not None
    token, _ = result
    return {"Authorization": f"Bearer {token}"}

def test_analyze_is_ephemeral_and_returns_complete_contract() -> None:
    response = client.post("/api/analyze", json={"text": "Segera kirim OTP atau akun diblokir", "source": "test"})
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "HIGH"
    assert len(body["nseae_scores"]) == 6
    assert body["recommendation"]
    assert body["model_source"] in {"indobert+nseae", "rules-fallback", "rules-fallback+nseae"}
    assert 0 <= body["model_confidence"] <= 1
    assert 0 <= body["nseae_risk_score"] <= 1
    assert isinstance(body["fusion_applied"], bool)

def test_report_requires_explicit_consent() -> None:
    response = client.post("/api/report", json={"text": "contoh", "category_suggested": "Social Engineering", "consent": False})
    assert response.status_code == 400

def test_public_content_endpoints() -> None:
    assert len(client.get("/api/categories").json()) == 5
    assert len(client.get("/api/education").json()) >= 6
    stats = client.get("/api/stats")
    assert stats.status_code == 200
    assert {"total_analyzed", "category_counts", "month_total", "month_category_counts", "top_category_this_month", "daily_stats", "updated_at"} <= stats.json().keys()


def test_wedding_invitation_apk_variations_are_phishing() -> None:
    messages = [
        "Undangan pernikahan.apk mohon dibuka",
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


def test_protective_warning_is_not_flagged_as_fraud(monkeypatch, tmp_path) -> None:
    from app.services.predictor import _pipeline
    monkeypatch.setenv("NUSAGUARD_MODEL_PATH", str(tmp_path / "missing-model"))
    _pipeline.cache_clear()
    try:
        response = client.post("/api/analyze", json={"text": "Jangan pernah kirim OTP, PIN, atau kata sandi kepada siapa pun."})
        body = response.json()
        assert response.status_code == 200
        assert body["category"] == "Aman"
        assert body["model_source"] == "rules-fallback+nseae"
        assert body["fusion_applied"] is True
    finally:
        _pipeline.cache_clear()


def test_admin_dashboard_requires_admin_role_and_supports_moderation() -> None:
    assert client.get("/api/admin/dashboard").status_code == 401
    assert client.get("/api/admin/dashboard", headers=auth_headers("user")).status_code == 403

    created = client.post("/api/report", json={
        "text": "Undangan palsu untuk ditinjau admin",
        "category_suggested": "Phishing/Link Berbahaya",
        "consent": True,
    })
    headers = auth_headers()
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


def test_user_registration_login_and_role_management() -> None:
    email = f"user-{uuid4().hex[:8]}@example.com"
    registered = client.post("/api/auth/register", json={"name": "Pengguna Uji", "email": email, "password": "rahasia123"})
    assert registered.status_code == 201
    assert registered.json()["user"]["role"] == "user"
    assert "analyze" in registered.json()["user"]["permissions"]

    token = registered.json()["access_token"]
    profile = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == email

    headers = auth_headers()
    users = client.get("/api/admin/users", headers=headers)
    target = next(item for item in users.json() if item["email"] == email)
    promoted = client.patch(f"/api/admin/users/{target['id']}", headers=headers, json={"role": "analyst"})
    assert promoted.status_code == 200
    assert "view_aggregate_stats" in promoted.json()["permissions"]

    login = client.post("/api/auth/login", json={"email": email, "password": "rahasia123"})
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "analyst"

    managed_email = f"managed-{uuid4().hex[:8]}@example.com"
    created_by_admin = client.post("/api/admin/users", headers=headers, json={"name": "Managed User", "email": managed_email, "password": "password123", "role": "user"})
    assert created_by_admin.status_code == 201
    managed_id = created_by_admin.json()["id"]
    updated_email = f"updated-{uuid4().hex[:8]}@example.com"
    edited = client.patch(f"/api/admin/users/{managed_id}", headers=headers, json={"name": "Updated User", "email": updated_email, "password": "password456", "role": "moderator", "is_active": False})
    assert edited.status_code == 200
    assert edited.json()["name"] == "Updated User"
    assert edited.json()["email"] == updated_email
    assert edited.json()["role"] == "moderator"
    assert edited.json()["is_active"] is False
    assert client.delete(f"/api/admin/users/{managed_id}", headers=headers).status_code == 204


def test_dynamic_education_and_anonymized_dataset() -> None:
    headers = auth_headers()
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


def test_dataset_collections_are_described_separately() -> None:
    info = client.get("/api/dataset/info")
    assert info.status_code == 200
    assert info.json()["development_samples"] == 3000
    assert info.json()["development_samples_per_category"] == 500
    assert info.json()["development_downloadable"] is False


def test_admin_candidate_workflow_and_activity_log() -> None:
    headers = auth_headers()
    created = client.post("/api/admin/candidates", headers=headers, json={
        "text_anonymized": "Segera kirim [KREDENSIAL] ke petugas palsu",
        "category": "Social Engineering",
        "source": "manual_test",
        "data_type": "primer",
        "validation_status": "pending",
        "split": None,
        "notes": "Perlu validasi",
        "is_duplicate": False,
        "is_archived": False,
        "nseae_validation": {"urgency": True, "credential_request": True},
    })
    assert created.status_code == 201
    candidate_id = created.json()["id"]
    updated = client.patch(f"/api/admin/candidates/{candidate_id}", headers=headers, json={**created.json(), "validation_status": "verified", "split": "train"})
    assert updated.status_code == 200
    assert updated.json()["validation_status"] == "verified"
    assert updated.json()["split"] == "train"
    assert any(item["id"] == candidate_id for item in client.get("/api/admin/candidates", headers=headers).json())
    assert client.get("/api/admin/activities", headers=headers).status_code == 200
    assert client.delete(f"/api/admin/candidates/{candidate_id}", headers=headers).status_code == 204

