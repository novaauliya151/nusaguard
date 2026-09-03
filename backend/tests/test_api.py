from fastapi.testclient import TestClient
from app.main import app
from app.services.store import admin_domain, store
from uuid import uuid4

client = TestClient(app)

def test_readiness_reports_database_and_model_policy() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] is True
    assert {"status", "indobert_configured", "indobert_required", "fallback_allowed"} <= response.json().keys()

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


def test_short_neutral_messages_are_safe_without_loading_model(monkeypatch) -> None:
    from app.services import predictor
    monkeypatch.setattr(predictor, "predict_probabilities", lambda _text: (_ for _ in ()).throw(AssertionError("model should not load")))
    for message in ("cobalah ini aja", "oke", "nanti aku kabari", "sudah sampai belum?", "aku sayang kamu"):
        response = client.post("/api/analyze", json={"text": message})
        assert response.status_code == 200
        body = response.json()
        assert body["category"] == "Aman"
        assert body["risk_level"] == "LOW"
        assert body["model_source"] == "low-information-guard"


def test_confident_model_cannot_flag_evidence_free_neutral_text(monkeypatch) -> None:
    from app.models.schemas import KategoriNusaGuard
    from app.services import predictor
    monkeypatch.setattr(predictor, "predict_probabilities", lambda _text: ({
        KategoriNusaGuard.PENIPUAN_ROMANSA: 0.99,
        KategoriNusaGuard.AMAN: 0.01,
    }, "indobert"))
    response = client.post("/api/analyze", json={"text": "Aku senang bisa berbicara denganmu malam ini"})
    assert response.status_code == 200
    assert response.json()["category"] == "Aman"


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


def test_admin_route_requires_authentication_and_permission() -> None:
    assert client.get("/api/admin/users").status_code == 401
    editor = auth_headers("content_editor")
    assert client.get("/api/admin/users", headers=editor).status_code == 403
    assert client.get("/api/admin/education", headers=editor).status_code == 200


def test_suspended_account_cannot_login_and_session_is_revoked() -> None:
    admin = auth_headers()
    email = f"blocked-{uuid4().hex[:8]}@example.com"
    created = client.post("/api/admin/users", headers=admin, json={"name":"Blocked User","email":email,"password":"password123","confirm_password":"password123","role":"validator"})
    assert created.status_code == 201
    token = client.post("/api/auth/login", json={"email":email,"password":"password123"}).json()["access_token"]
    blocked = client.patch(f"/api/admin/users/{created.json()['id']}", headers=admin, json={"status":"suspended","suspension_reason":"Pengujian"})
    assert blocked.status_code == 200
    assert client.get("/api/auth/me", headers={"Authorization":f"Bearer {token}"}).status_code == 401
    assert client.post("/api/auth/login", json={"email":email,"password":"password123"}).status_code == 401


def test_nseae_human_validation_is_stored_separately() -> None:
    headers = auth_headers()
    candidate = client.post("/api/admin/candidates", headers=headers, json={"text_anonymized":"Segera verifikasi melalui kanal resmi.","category":"Social Engineering","source":"test","data_type":"primer","validation_status":"pending","split":"train","notes":"uji","is_duplicate":False,"is_archived":False,"nseae_validation":{"urgency":True}})
    assert candidate.status_code == 201
    indicators = ["urgency","authority","fear","reward","impersonation","credential_request"]
    payload = {"validations":[{"indicator":name,"ai_score":0.8 if name=="urgency" else 0,"human_validation":"detected" if name=="urgency" else "not_detected","detected_evidence":"segera" if name=="urgency" else "","notes":""} for name in indicators]}
    saved = client.put(f"/api/admin/nseae-validations/{candidate.json()['id']}", headers=headers, json=payload)
    assert saved.status_code == 200
    assert len(saved.json()) == 6
    unchanged = client.get("/api/admin/candidates", headers=headers).json()
    row = next(item for item in unchanged if item["id"] == candidate.json()["id"])
    assert row["nseae_validation"] == {"urgency": True}


def test_education_draft_and_dataset_export_are_privacy_safe() -> None:
    headers = auth_headers()
    draft = client.post("/api/admin/education", headers=headers, json={"title":"Draft Edukasi Aman","category":"Aman","description":"Konten edukasi ini masih berupa draft internal.","warning_signs":["Tidak meminta data"],"prevention":["Tetap verifikasi"],"is_published":False,"status":"draft"})
    assert draft.status_code == 201
    assert draft.json()["status"] == "draft"
    assert not any(item["id"] == draft.json()["id"] for item in client.get("/api/education").json())
    exported = client.get("/api/admin/candidates/export", headers=headers)
    assert exported.status_code == 200
    assert "text_anonymized" in exported.text.splitlines()[0]

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
    assert all(item.get("report_id") != report["id"] for item in store.public_dataset())
    candidate_id = processed.json()["id"]
    validations = [{"indicator": indicator, "ai_score": 0.5, "human_validation": "detected", "detected_evidence": "frasa anonim", "notes": "ditinjau"} for indicator in ("urgency", "authority", "fear", "reward", "impersonation", "credential_request")]
    assert client.put(f"/api/admin/nseae-validations/{candidate_id}", headers=headers, json={"validations": validations}).status_code == 200
    verified = client.patch(f"/api/admin/candidates/{candidate_id}", headers=headers, json={**processed.json(), "validation_status": "verified", "split": "train"})
    assert verified.status_code == 200
    assert client.post(f"/api/admin/candidates/{candidate_id}/publish", headers=headers).status_code == 201
    assert any(item["id"] for item in client.get("/api/dataset").json())


def test_dataset_collections_are_described_separately() -> None:
    info = client.get("/api/dataset/info")
    assert info.status_code == 200
    assert info.json()["development_samples"] == 3600
    assert info.json()["development_samples_per_category"] == 600
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
    validations = [{"indicator": indicator, "ai_score": 0.5, "human_validation": "not_detected", "detected_evidence": "", "notes": "ditinjau"} for indicator in ("urgency", "authority", "fear", "reward", "impersonation", "credential_request")]
    assert client.put(f"/api/admin/nseae-validations/{candidate_id}", headers=headers, json={"validations": validations}).status_code == 200
    updated = client.patch(f"/api/admin/candidates/{candidate_id}", headers=headers, json={**created.json(), "validation_status": "verified", "split": "train"})
    assert updated.status_code == 200
    assert updated.json()["validation_status"] == "verified"
    assert updated.json()["split"] == "train"
    assert any(item["id"] == candidate_id for item in client.get("/api/admin/candidates", headers=headers).json())
    assert client.get("/api/admin/activities", headers=headers).status_code == 200
    assert client.delete(f"/api/admin/candidates/{candidate_id}", headers=headers).status_code == 204


def test_guest_remains_ephemeral_and_user_history_is_owner_scoped() -> None:
    before = store.engine.connect().execute(__import__("sqlalchemy").text("SELECT COUNT(*) FROM user_analysis_histories")).scalar_one()
    assert client.post("/api/analyze", json={"text":"Jangan kirim OTP"}).status_code == 200
    after = store.engine.connect().execute(__import__("sqlalchemy").text("SELECT COUNT(*) FROM user_analysis_histories")).scalar_one()
    assert after == before
    first = client.post("/api/auth/register", json={"name":"User Satu","email":f"one-{uuid4().hex}@example.com","password":"aman12345","confirm_password":"aman12345","accept_terms":True,"accept_privacy":True}).json()
    second = client.post("/api/auth/register", json={"name":"User Dua","email":f"two-{uuid4().hex}@example.com","password":"aman12345","confirm_password":"aman12345","accept_terms":True,"accept_privacy":True}).json()
    first_headers={"Authorization":f"Bearer {first['access_token']}"};second_headers={"Authorization":f"Bearer {second['access_token']}"}
    saved=client.post("/api/user/histories",headers=first_headers,json={"text":"OTP 123456 kirim ke test@example.com","category":"Social Engineering","risk_level":"HIGH","risk_score":.9,"confidence":.8,"summary":"Uji","nseae_scores":{"credential_request":1}})
    assert saved.status_code==201 and "123456" not in (saved.json()["anonymized_text"] or "") and "test@example.com" not in saved.json()["anonymized_text"]
    history_id=saved.json()["id"]
    assert client.get(f"/api/user/histories/{history_id}",headers=first_headers).status_code==200
    assert client.get(f"/api/user/histories/{history_id}",headers=second_headers).status_code==404
    assert client.patch(f"/api/user/histories/{history_id}",headers=first_headers,json={"is_favorite":True,"personal_note":"Penting"}).json()["is_favorite"] is True
    assert client.delete(f"/api/user/histories/{history_id}",headers=second_headers).status_code==404
    assert client.delete(f"/api/user/histories/{history_id}",headers=first_headers).status_code==204


def test_user_privacy_reports_guides_and_export_are_private() -> None:
    email=f"privacy-{uuid4().hex}@example.com";registered=client.post("/api/auth/register",json={"name":"Privacy User","email":email,"password":"aman12345"}).json();headers={"Authorization":f"Bearer {registered['access_token']}"}
    settings=client.put("/api/user/privacy",headers=headers,json={"history_storage_mode":"never","retention_period":"30_days","save_anonymized_text":False,"require_save_confirmation":True})
    assert settings.status_code==200
    assert client.post("/api/user/histories",headers=headers,json={"text":"rahasia","category":"Aman","risk_level":"LOW","risk_score":.1}).status_code==409
    report=client.post("/api/report",headers=headers,json={"text":"Hubungi 081234567890","category_suggested":"Social Engineering","consent":True})
    assert report.status_code==201 and any(x["id"]==report.json()["id"] for x in client.get("/api/user/reports",headers=headers).json())
    guide=client.get("/api/education").json()[0]
    assert client.post(f"/api/user/saved-guides/{guide['id']}",headers=headers).status_code==204
    assert any(x["id"]==guide["id"] for x in client.get("/api/user/saved-guides",headers=headers).json())
    exported=client.get("/api/user/data-export",headers=headers).json()
    assert "password_hash" not in str(exported) and "token" not in str(exported)
    assert client.get("/api/admin/dashboard",headers=headers).status_code==403


def test_admin_settings_control_runtime_services() -> None:
    admin_domain.save_settings({"analysis": {"service_enabled": "false"}}, "test")
    try:
        response = client.post("/api/analyze", json={"text": "pesan uji"})
        assert response.status_code == 503
    finally:
        admin_domain.save_settings({"analysis": {"service_enabled": "true"}}, "test")
    assert client.post("/api/analyze", json={"text": "pesan uji"}).status_code == 200


def test_admin_lexicon_and_recommendation_affect_live_analysis() -> None:
    headers = auth_headers()
    phrase = f"sinyalunik{uuid4().hex[:8]}"
    lexicon = client.post("/api/admin/lexicons", headers=headers, json={"phrase": phrase, "indicator": "fear", "weight": 1, "match_type": "contains", "example": "", "description": "uji runtime", "is_active": True})
    assert lexicon.status_code == 201
    recommendation = client.post("/api/admin/recommendations", headers=headers, json={"title": f"Rekomendasi {phrase}", "content": "REKOMENDASI DINAMIS TERHUBUNG", "category": None, "risk_level": None, "nseae_indicator": "fear", "display_order": 0, "is_active": True})
    assert recommendation.status_code == 201
    analyzed = client.post("/api/analyze", json={"text": phrase})
    assert analyzed.status_code == 200
    assert analyzed.json()["nseae_scores"]["fear"] == 1
    assert analyzed.json()["recommendation"] == "REKOMENDASI DINAMIS TERHUBUNG"
    logs = client.get("/api/admin/activities", headers=headers).json()
    assert any(item.get("ip_address") for item in logs)


def test_custom_role_can_be_assigned_and_authorized() -> None:
    headers = auth_headers()
    slug = f"reviewer_{uuid4().hex[:8]}"
    role = client.post("/api/admin/roles", headers=headers, json={"name": "Reviewer Khusus", "slug": slug, "description": "Role kustom", "permissions": ["dashboard.view"]})
    assert role.status_code == 201
    email = f"{slug}@example.com"
    created = client.post("/api/admin/users", headers=headers, json={"name": "Reviewer", "email": email, "password": "rahasia123", "confirm_password": "rahasia123", "role": slug, "status": "active", "must_change_password": False})
    assert created.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": "rahasia123"})
    assert login.status_code == 200
    custom_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/admin/dashboard", headers=custom_headers).status_code == 200


