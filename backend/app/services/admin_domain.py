"""Fondasi domain admin: schema, RBAC, seed, dan operasi lintas modul.

Modul ini sengaja memakai engine Store yang sudah ada agar migrasi tetap kompatibel
dengan instalasi SQLite lama serta DATABASE_URL PostgreSQL tanpa mengganti stack.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from app.services.request_context import request_agent, request_ip

PERMISSIONS = {
    "dashboard.view": ("Dashboard", "dashboard"),
    "users.view": ("Lihat pengguna", "users"), "users.create": ("Tambah pengguna", "users"),
    "users.update": ("Ubah pengguna", "users"), "users.suspend": ("Blokir pengguna", "users"),
    "users.delete": ("Hapus pengguna", "users"), "roles.manage": ("Kelola role", "roles"),
    "reports.view": ("Lihat laporan", "reports"), "reports.review": ("Tinjau laporan", "reports"),
    "reports.approve": ("Setujui laporan", "reports"), "reports.reject": ("Tolak laporan", "reports"),
    "reports.anonymize": ("Anonimisasi laporan", "reports"),
    "datasets.view": ("Lihat dataset", "datasets"), "datasets.create": ("Tambah dataset", "datasets"),
    "datasets.update": ("Ubah dataset", "datasets"), "datasets.validate": ("Validasi dataset", "datasets"),
    "datasets.import": ("Impor dataset", "datasets"), "datasets.export": ("Ekspor dataset", "datasets"),
    "datasets.archive": ("Arsip dataset", "datasets"), "nseae.validate": ("Validasi N-SEAE", "nseae"),
    "lexicons.view": ("Lihat leksikon", "lexicons"), "lexicons.manage": ("Kelola leksikon", "lexicons"),
    "education.view": ("Lihat edukasi", "education"), "education.create": ("Tambah edukasi", "education"),
    "education.update": ("Ubah edukasi", "education"), "education.publish": ("Publikasi edukasi", "education"),
    "education.delete": ("Hapus edukasi", "education"),
    "recommendations.manage": ("Kelola rekomendasi", "recommendations"),
    "statistics.view": ("Lihat statistik", "statistics"), "models.view": ("Lihat model", "models"),
    "models.test": ("Uji model", "models"), "models.manage": ("Kelola versi model", "models"), "activity_logs.view": ("Lihat log", "activity_logs"),
    "settings.manage": ("Kelola pengaturan", "settings"), "profile.manage": ("Kelola profil", "profile"),
    "dashboard.user.view": ("Dashboard pribadi", "user"), "analysis.create": ("Analisis pesan", "user"),
    "analysis.history.view_own": ("Lihat riwayat sendiri", "user"), "analysis.history.delete_own": ("Hapus riwayat sendiri", "user"),
    "analysis.history.export_own": ("Ekspor riwayat sendiri", "user"), "analysis.favorite.manage_own": ("Kelola penanda penting", "user"),
    "reports.create": ("Kirim laporan", "user"), "reports.view_own": ("Lihat laporan sendiri", "user"),
    "guides.favorite.manage_own": ("Simpan panduan", "user"), "profile.view_own": ("Lihat profil sendiri", "user"),
    "profile.update_own": ("Ubah profil sendiri", "user"), "account.password.update_own": ("Ubah kata sandi sendiri", "user"),
    "account.delete_own": ("Hapus akun sendiri", "user"), "privacy.settings.update_own": ("Atur privasi sendiri", "user"),
}

ROLE_DEFINITIONS = {
    "super_admin": {"name": "Super Admin", "permissions": set(PERMISSIONS)},
    "validator": {"name": "Admin/Validator", "permissions": {
        "dashboard.view", "reports.view", "reports.review", "reports.approve", "reports.reject",
        "reports.anonymize", "datasets.view", "datasets.create", "datasets.update", "datasets.validate",
        "datasets.import", "datasets.export", "datasets.archive", "nseae.validate", "lexicons.view",
        "lexicons.manage", "statistics.view", "models.view", "models.test", "profile.manage",
    }},
    "content_editor": {"name": "Editor Konten", "permissions": {
        "dashboard.view", "education.view", "education.create", "education.update", "education.publish",
        "education.delete", "recommendations.manage", "profile.manage",
    }},
    "user": {"name": "Pengguna", "permissions": {slug for slug in PERMISSIONS if slug.endswith("_own") or slug in {"dashboard.user.view","analysis.create","reports.create"}}},
}
ROLE_ALIASES = {"admin": "super_admin", "moderator": "validator", "analyst": "validator"}
LEGACY_PERMISSIONS = {"analyst": ["view_aggregate_stats"], "moderator": ["view_aggregate_stats", "manage_reports"], "admin": ["manage_users", "manage_reports", "view_system_status"]}
INDICATORS = ("urgency", "authority", "fear", "reward", "impersonation", "credential_request")
CATEGORIES = ("Aman", "Phishing/Link Berbahaya", "Social Engineering", "Penipuan Investasi", "Penipuan Rekrutmen", "Penipuan Romansa")


def canonical_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


class AdminDomain:
    def __init__(self, store: Any) -> None:
        self.store = store
        self.engine = store.engine
        self.initialize()

    def initialize(self) -> None:
        now = datetime.now(timezone.utc)
        with self.engine.begin() as db:
            ddl = [
                "CREATE TABLE IF NOT EXISTS roles (id VARCHAR(36) PRIMARY KEY, name VARCHAR(80) NOT NULL, slug VARCHAR(40) NOT NULL UNIQUE, description TEXT, is_system BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)",
                "CREATE TABLE IF NOT EXISTS permissions (id VARCHAR(36) PRIMARY KEY, name VARCHAR(100) NOT NULL, slug VARCHAR(80) NOT NULL UNIQUE, module VARCHAR(50) NOT NULL, description TEXT)",
                "CREATE TABLE IF NOT EXISTS role_permissions (role_id VARCHAR(36) NOT NULL, permission_id VARCHAR(36) NOT NULL, PRIMARY KEY(role_id,permission_id), FOREIGN KEY(role_id) REFERENCES roles(id), FOREIGN KEY(permission_id) REFERENCES permissions(id))",
                "CREATE TABLE IF NOT EXISTS nseae_validations (id VARCHAR(36) PRIMARY KEY, dataset_candidate_id VARCHAR(36) NOT NULL, indicator VARCHAR(40) NOT NULL, ai_score FLOAT NOT NULL DEFAULT 0, human_validation VARCHAR(20) NOT NULL, detected_evidence TEXT, validator_id VARCHAR(36), notes TEXT, validated_at TIMESTAMP NOT NULL, UNIQUE(dataset_candidate_id,indicator), FOREIGN KEY(dataset_candidate_id) REFERENCES dataset_candidates(id))",
                "CREATE TABLE IF NOT EXISTS nseae_lexicons (id VARCHAR(36) PRIMARY KEY, phrase VARCHAR(240) NOT NULL, indicator VARCHAR(40) NOT NULL, weight FLOAT NOT NULL, match_type VARCHAR(20) NOT NULL, example TEXT, description TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE, created_by VARCHAR(36), created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL, deleted_at TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS action_recommendations (id VARCHAR(36) PRIMARY KEY, title VARCHAR(160) NOT NULL, content TEXT NOT NULL, category VARCHAR(80), risk_level VARCHAR(20), nseae_indicator VARCHAR(40), display_order INTEGER NOT NULL DEFAULT 0, is_active BOOLEAN NOT NULL DEFAULT TRUE, created_by VARCHAR(36), created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL, deleted_at TIMESTAMP)",
                "CREATE TABLE IF NOT EXISTS model_versions (id VARCHAR(36) PRIMARY KEY, model_name VARCHAR(120) NOT NULL, version VARCHAR(80) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'inactive', accuracy FLOAT, precision_score FLOAT, recall_score FLOAT, f1_score FLOAT, evaluation_dataset VARCHAR(240), evaluated_at TIMESTAMP, notes TEXT, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL, UNIQUE(model_name,version))",
                "CREATE TABLE IF NOT EXISTS analysis_statistics (id VARCHAR(36) PRIMARY KEY, category VARCHAR(80) NOT NULL, risk_level VARCHAR(20) NOT NULL, processing_status VARCHAR(20) NOT NULL, response_time_ms FLOAT NOT NULL, detected_indicators TEXT NOT NULL, model_version VARCHAR(80), analyzed_at TIMESTAMP NOT NULL)",
                "CREATE TABLE IF NOT EXISTS system_settings (id VARCHAR(36) PRIMARY KEY, setting_group VARCHAR(40) NOT NULL, setting_key VARCHAR(80) NOT NULL, value TEXT NOT NULL, value_type VARCHAR(20) NOT NULL, is_public BOOLEAN NOT NULL DEFAULT FALSE, updated_by VARCHAR(36), updated_at TIMESTAMP NOT NULL, UNIQUE(setting_group,setting_key))",
            ]
            for statement in ddl:
                db.execute(text(statement))
            self._ensure_columns(db)
            for slug, definition in ROLE_DEFINITIONS.items():
                db.execute(text("INSERT INTO roles(id,name,slug,description,is_system,created_at,updated_at) SELECT :id,:name,:slug,:description,TRUE,:now,:now WHERE NOT EXISTS (SELECT 1 FROM roles WHERE slug=:slug)"), {"id": str(uuid.uuid4()), "name": definition["name"], "slug": slug, "description": f"Role sistem {definition['name']}", "now": now})
            for slug, (name, module) in PERMISSIONS.items():
                db.execute(text("INSERT INTO permissions(id,name,slug,module,description) SELECT :id,:name,:slug,:module,:description WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE slug=:slug)"), {"id": str(uuid.uuid4()), "name": name, "slug": slug, "module": module, "description": name})
            for role_slug, definition in ROLE_DEFINITIONS.items():
                for permission in definition["permissions"]:
                    db.execute(text("INSERT INTO role_permissions(role_id,permission_id) SELECT r.id,p.id FROM roles r,permissions p WHERE r.slug=:role AND p.slug=:permission AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id=r.id AND rp.permission_id=p.id)"), {"role": role_slug, "permission": permission})
            self._seed_reference(db, now)
        self._seed_initial_admin()

    def _ensure_columns(self, db: Any) -> None:
        backend = self.engine.url.get_backend_name()
        additions = {
            "users": {"status": "VARCHAR(20) NOT NULL DEFAULT 'active'", "avatar": "TEXT", "must_change_password": "BOOLEAN NOT NULL DEFAULT FALSE", "last_login_at": "TIMESTAMP", "suspended_at": "TIMESTAMP", "suspended_by": "VARCHAR(36)", "suspension_reason": "TEXT", "created_by": "VARCHAR(36)", "updated_at": "TIMESTAMP", "deleted_at": "TIMESTAMP"},
            "dataset_candidates": {"deleted_at": "TIMESTAMP", "annotation_version": "VARCHAR(40) NOT NULL DEFAULT '1.0'", "validated_at": "TIMESTAMP"},
            "admin_activity_logs": {"user_id": "VARCHAR(36)", "module": "VARCHAR(50)", "entity_type": "VARCHAR(50)", "old_values": "TEXT", "new_values": "TEXT", "ip_address": "VARCHAR(64)", "user_agent": "TEXT"},
            "education_items": {"slug": "VARCHAR(160)", "summary": "TEXT", "content": "TEXT", "anonymized_example": "TEXT", "response_steps": "TEXT", "thumbnail": "TEXT", "image_alt": "VARCHAR(240)", "meta_title": "VARCHAR(160)", "meta_description": "TEXT", "status": "VARCHAR(20) NOT NULL DEFAULT 'published'", "published_at": "TIMESTAMP", "author_id": "VARCHAR(36)", "display_order": "INTEGER NOT NULL DEFAULT 0", "deleted_at": "TIMESTAMP"},
            "reports": {"predicted_category": "VARCHAR(80)", "risk_score": "FLOAT", "confidence_score": "FLOAT", "nseae_scores": "TEXT", "reviewer_id": "VARCHAR(36)", "reviewed_at": "TIMESTAMP", "rejection_reason": "TEXT", "duplicate_of": "VARCHAR(36)", "anonymized_text": "TEXT", "updated_at": "TIMESTAMP", "deleted_at": "TIMESTAMP"},
        }
        if backend == "sqlite":
            for table, columns in additions.items():
                existing = {row[1] for row in db.execute(text(f"PRAGMA table_info({table})"))}
                for name, definition in columns.items():
                    if name not in existing:
                        db.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        elif backend.startswith("postgresql"):
            for table, columns in additions.items():
                for name, definition in columns.items():
                    db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {definition}"))

    def _seed_reference(self, db: Any, now: datetime) -> None:
        settings = {
            ("general", "app_name"): ("NusaGuard", "string", True), ("general", "help_email"): ("", "string", True),
            ("analysis", "min_characters"): ("1", "integer", False), ("analysis", "max_characters"): ("5000", "integer", False),
            ("analysis", "service_enabled"): ("true", "boolean", False), ("reports", "form_enabled"): ("true", "boolean", True),
            ("public_statistics", "enabled"): ("true", "boolean", True), ("system", "maintenance_mode"): ("false", "boolean", False),
            ("system", "app_version"): ("1.0.0", "string", True), ("system", "timezone"): ("Asia/Jakarta", "string", False),
        }
        for (group, key), (value, value_type, public) in settings.items():
            db.execute(text("INSERT INTO system_settings(id,setting_group,setting_key,value,value_type,is_public,updated_at) SELECT :id,:group,:key,:value,:type,:public,:now WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE setting_group=:group AND setting_key=:key)"), {"id": str(uuid.uuid4()), "group": group, "key": key, "value": value, "type": value_type, "public": public, "now": now})
        lexicons = [("segera", "urgency", .7), ("atas nama", "authority", .6), ("akun diblokir", "fear", .8), ("hadiah", "reward", .6), ("saya dari bank", "impersonation", .9), ("kirim otp", "credential_request", 1.0)]
        for phrase, indicator, weight in lexicons:
            db.execute(text("INSERT INTO nseae_lexicons(id,phrase,indicator,weight,match_type,example,description,is_active,created_at,updated_at) SELECT :id,:phrase,:indicator,:weight,'contains','',:description,TRUE,:now,:now WHERE NOT EXISTS (SELECT 1 FROM nseae_lexicons WHERE phrase=:phrase AND indicator=:indicator AND deleted_at IS NULL)"), {"id": str(uuid.uuid4()), "phrase": phrase, "indicator": indicator, "weight": weight, "description": "Leksikon awal NusaGuard", "now": now})
        recommendations = [("Jaga kredensial", "Jangan memberikan OTP, PIN, password, atau kode verifikasi kepada siapa pun.", None, "HIGH", "credential_request"), ("Hindari tautan asing", "Jangan membuka tautan atau file dari pengirim yang belum terverifikasi.", "Phishing/Link Berbahaya", None, None), ("Verifikasi identitas", "Hubungi pihak terkait melalui nomor resmi, bukan nomor yang mengirim pesan.", None, None, "impersonation")]
        for order, (title, content, category, risk, indicator) in enumerate(recommendations):
            db.execute(text("INSERT INTO action_recommendations(id,title,content,category,risk_level,nseae_indicator,display_order,is_active,created_at,updated_at) SELECT :id,:title,:content,:category,:risk,:indicator,:order,TRUE,:now,:now WHERE NOT EXISTS (SELECT 1 FROM action_recommendations WHERE title=:title AND deleted_at IS NULL)"), {"id": str(uuid.uuid4()), "title": title, "content": content, "category": category, "risk": risk, "indicator": indicator, "order": order, "now": now})
        db.execute(text("INSERT INTO model_versions(id,model_name,version,status,accuracy,precision_score,recall_score,f1_score,evaluation_dataset,evaluated_at,notes,created_at,updated_at) SELECT :id,'IndoBERT NusaGuard','local-1','active',NULL,NULL,NULL,NULL,'Belum dicatat',NULL,'Nilai evaluasi harus diisi dari artefak evaluation.json, bukan diklaim dari data sintetis.',:now,:now WHERE NOT EXISTS (SELECT 1 FROM model_versions WHERE status='active')"), {"id":str(uuid.uuid4()),"now":now})

    def _seed_initial_admin(self) -> None:
        email, password = os.getenv("INITIAL_ADMIN_EMAIL"), os.getenv("INITIAL_ADMIN_PASSWORD")
        if not email or not password or self.store.get_user_by_email(email):
            return
        self.store.create_user(os.getenv("INITIAL_ADMIN_NAME", "Super Admin"), email, password, "super_admin")

    def permissions_for(self, role: str) -> list[str]:
        canonical = canonical_role(role)
        with self.engine.connect() as db:
            rows = db.execute(text("SELECT p.slug FROM permissions p JOIN role_permissions rp ON rp.permission_id=p.id JOIN roles r ON r.id=rp.role_id WHERE r.slug=:role ORDER BY p.slug"), {"role": canonical}).all()
        return [row[0] for row in rows]

    def list_users(self, query: str = "", role: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        clauses, params = ["u.deleted_at IS NULL"], {"query": f"%{query.casefold()}%"}
        if query: clauses.append("(lower(u.name) LIKE :query OR lower(u.email) LIKE :query)")
        if role: clauses.append("u.role=:role"); params["role"] = role
        if status: clauses.append("u.status=:status"); params["status"] = status
        with self.engine.connect() as db:
            rows = db.execute(text(f"SELECT u.id,u.name,u.email,u.role,u.status,u.is_active,u.avatar,u.must_change_password,u.email_verified_at,u.last_login_at,u.created_by,u.created_at,u.updated_at,c.name AS created_by_name,(SELECT COUNT(*) FROM user_analysis_histories h WHERE h.user_id=u.id AND h.deleted_at IS NULL) AS analysis_count,(SELECT COUNT(*) FROM reports r WHERE r.user_id=u.id AND r.deleted_at IS NULL) AS report_count FROM users u LEFT JOIN users c ON c.id=u.created_by WHERE {' AND '.join(clauses)} ORDER BY u.created_at DESC"), params).mappings().all()
        return [{**dict(row), "is_active": bool(row["is_active"]), "must_change_password": bool(row["must_change_password"]), "permissions": sorted(set(self.permissions_for(row["role"]) + LEGACY_PERMISSIONS.get(row["role"], [])))} for row in rows]

    def user_detail(self, user_id: str) -> dict[str, Any] | None:
        rows = [row for row in self.list_users() if row["id"] == user_id]
        if not rows: return None
        item = rows[0]
        with self.engine.connect() as db:
            item["activities"] = [dict(row) for row in db.execute(text("SELECT * FROM admin_activity_logs WHERE user_id=:id OR admin_email=:email ORDER BY created_at DESC LIMIT 20"), {"id": user_id, "email": item["email"]}).mappings().all()]
        return item

    def create_internal_user(self, payload: dict[str, Any], actor_id: str) -> dict[str, Any] | None:
        requested_role, role = payload["role"], canonical_role(payload["role"])
        if not any(item["slug"] == role for item in self.roles()): raise ValueError("Role tidak valid.")
        role = requested_role if requested_role in ROLE_ALIASES else role
        user = self.store.create_user(payload["name"], payload["email"], payload["password"], role)
        if not user: return None
        now = datetime.now(timezone.utc); status = payload.get("status", "active")
        with self.engine.begin() as db:
            db.execute(text("UPDATE users SET status=:status,is_active=:active,must_change_password=:must_change,created_by=:actor,updated_at=:now WHERE id=:id"), {"status": status, "active": status == "active", "must_change": payload.get("must_change_password", True), "actor": actor_id, "now": now, "id": user["id"]})
        return self.user_detail(user["id"])

    def _super_admin_count(self) -> int:
        with self.engine.connect() as db:
            return int(db.execute(text("SELECT COUNT(*) FROM users WHERE role IN ('super_admin','admin') AND status='active' AND deleted_at IS NULL")).scalar_one())

    def update_internal_user(self, user_id: str, payload: dict[str, Any], actor: dict[str, Any]) -> dict[str, Any]:
        target = self.user_detail(user_id)
        if not target: raise LookupError("Pengguna tidak ditemukan.")
        requested_role = payload.get("role", target["role"]); canonical = canonical_role(requested_role); role = requested_role if requested_role in ROLE_ALIASES else canonical; status = payload.get("status", target["status"])
        if not any(item["slug"] == canonical for item in self.roles()): raise ValueError("Role tidak valid.")
        if actor["id"] == user_id and (canonical_role(role) != canonical_role(target["role"]) or status != "active"): raise ValueError("Anda tidak dapat mengubah role atau menonaktifkan akun sendiri.")
        if canonical_role(target["role"]) == "super_admin" and self._super_admin_count() <= 1 and (canonical_role(role) != "super_admin" or status != "active"): raise ValueError("Super Admin terakhir tidak boleh diturunkan atau diblokir.")
        now = datetime.now(timezone.utc); updates = ["role=:role", "status=:status", "is_active=:active", "updated_at=:now"]; params: dict[str, Any] = {"id": user_id, "role": role, "status": status, "active": status == "active", "now": now}
        for field in ("name", "email", "avatar", "must_change_password"):
            if field in payload and payload[field] is not None: updates.append(f"{field}=:{field}"); params[field] = payload[field].casefold() if field == "email" else payload[field]
        if status == "suspended": updates += ["suspended_at=:now", "suspended_by=:actor", "suspension_reason=:reason"]; params.update(actor=actor["id"], reason=payload.get("suspension_reason"))
        try:
            with self.engine.begin() as db:
                db.execute(text(f"UPDATE users SET {','.join(updates)} WHERE id=:id"), params)
                if status != "active": db.execute(text("DELETE FROM user_sessions WHERE user_id=:id"), {"id": user_id})
        except Exception as exc:
            if "unique" in str(exc).casefold(): raise ValueError("Email sudah digunakan.") from exc
            raise
        return self.user_detail(user_id)  # type: ignore[return-value]

    def reset_password(self, user_id: str, password: str, must_change: bool) -> None:
        if not self.user_detail(user_id): raise LookupError("Pengguna tidak ditemukan.")
        with self.engine.begin() as db:
            db.execute(text("UPDATE users SET password_hash=:password,must_change_password=:must_change,updated_at=:now WHERE id=:id"), {"password": self.store._password_hash(password), "must_change": must_change, "now": datetime.now(timezone.utc), "id": user_id})
            db.execute(text("DELETE FROM user_sessions WHERE user_id=:id"), {"id": user_id})

    def soft_delete_user(self, user_id: str, actor: dict[str, Any]) -> None:
        target = self.user_detail(user_id)
        if not target: raise LookupError("Pengguna tidak ditemukan.")
        if actor["id"] == user_id: raise ValueError("Anda tidak dapat menghapus akun sendiri.")
        if canonical_role(target["role"]) == "super_admin" and self._super_admin_count() <= 1: raise ValueError("Super Admin terakhir tidak boleh dihapus.")
        now = datetime.now(timezone.utc)
        with self.engine.begin() as db:
            db.execute(text("UPDATE users SET deleted_at=:now,status='inactive',is_active=FALSE,updated_at=:now WHERE id=:id"), {"now": now, "id": user_id})
            db.execute(text("DELETE FROM user_sessions WHERE user_id=:id"), {"id": user_id})

    def roles(self) -> list[dict[str, Any]]:
        with self.engine.connect() as db:
            rows = db.execute(text("SELECT r.*,COUNT(DISTINCT u.id) AS user_count FROM roles r LEFT JOIN users u ON u.role=r.slug AND u.deleted_at IS NULL GROUP BY r.id ORDER BY r.is_system DESC,r.name")).mappings().all()
            result = []
            for row in rows:
                item = dict(row); item["permissions"] = self.permissions_for(item["slug"]); result.append(item)
            return result

    def permission_catalog(self) -> list[dict[str, Any]]:
        with self.engine.connect() as db:
            return [dict(row) for row in db.execute(text("SELECT * FROM permissions ORDER BY module,name")).mappings().all()]

    def save_role(self, role_id: str | None, payload: dict[str, Any]) -> dict[str, Any]:
        now, slug = datetime.now(timezone.utc), re.sub(r"[^a-z0-9]+", "_", payload["slug"].casefold()).strip("_")
        with self.engine.begin() as db:
            if role_id:
                role = db.execute(text("SELECT * FROM roles WHERE id=:id"), {"id": role_id}).mappings().first()
                if not role: raise ValueError("Role tidak ditemukan.")
                if role["is_system"] and slug != role["slug"]: raise ValueError("Slug role sistem tidak dapat diubah.")
                db.execute(text("UPDATE roles SET name=:name,description=:description,updated_at=:now WHERE id=:id"), {"id": role_id, "name": payload["name"], "description": payload.get("description"), "now": now})
            else:
                role_id = str(uuid.uuid4()); db.execute(text("INSERT INTO roles(id,name,slug,description,is_system,created_at,updated_at) VALUES (:id,:name,:slug,:description,FALSE,:now,:now)"), {"id": role_id, "name": payload["name"], "slug": slug, "description": payload.get("description"), "now": now})
            db.execute(text("DELETE FROM role_permissions WHERE role_id=:id"), {"id": role_id})
            for permission in payload.get("permissions", []):
                db.execute(text("INSERT INTO role_permissions(role_id,permission_id) SELECT :id,id FROM permissions WHERE slug=:permission"), {"id": role_id, "permission": permission})
        return next(item for item in self.roles() if item["id"] == role_id)

    def record_analysis(self, category: str, risk: str, status: str, response_ms: float, indicators: list[str], model: str) -> None:
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO analysis_statistics(id,category,risk_level,processing_status,response_time_ms,detected_indicators,model_version,analyzed_at) VALUES (:id,:category,:risk,:status,:response,:indicators,:model,:now)"), {"id": str(uuid.uuid4()), "category": category, "risk": risk, "status": status, "response": response_ms, "indicators": json.dumps(indicators), "model": model, "now": datetime.now(timezone.utc)})

    def crud_list(self, table: str, include_deleted: bool = False) -> list[dict[str, Any]]:
        allowed = {"nseae_lexicons", "action_recommendations", "model_versions", "system_settings", "nseae_validations"}
        if table not in allowed: raise ValueError("Tabel tidak diizinkan")
        deleted = " WHERE deleted_at IS NULL" if not include_deleted and table in {"nseae_lexicons", "action_recommendations"} else ""
        with self.engine.connect() as db:
            return [dict(row) for row in db.execute(text(f"SELECT * FROM {table}{deleted} ORDER BY created_at DESC" if table not in {"system_settings", "nseae_validations"} else f"SELECT * FROM {table}{deleted} ORDER BY updated_at DESC" if table == "system_settings" else f"SELECT * FROM {table} ORDER BY validated_at DESC")).mappings().all()]

    def save_lexicon(self, item_id: str | None, payload: dict[str, Any], actor_id: str) -> dict[str, Any]:
        if payload["indicator"] not in INDICATORS: raise ValueError("Indikator N-SEAE tidak valid.")
        if payload["match_type"] == "regex":
            if len(payload["phrase"]) > 120 or re.search(r"\([^)]*[+*][^)]*\)[+*]", payload["phrase"]): raise ValueError("Pola regex berisiko atau terlalu panjang.")
            try: re.compile(payload["phrase"])
            except re.error as exc: raise ValueError("Regex tidak valid.") from exc
        now, item_id = datetime.now(timezone.utc), item_id or str(uuid.uuid4())
        params = {**payload, "id": item_id, "actor": actor_id, "now": now}
        with self.engine.begin() as db:
            duplicate = db.execute(text("SELECT id FROM nseae_lexicons WHERE lower(phrase)=lower(:phrase) AND indicator=:indicator AND deleted_at IS NULL AND id<>:id"), params).first()
            if duplicate: raise ValueError("Kata/frasa sudah tersedia untuk indikator ini.")
            if db.execute(text("SELECT 1 FROM nseae_lexicons WHERE id=:id"), {"id": item_id}).first():
                db.execute(text("UPDATE nseae_lexicons SET phrase=:phrase,indicator=:indicator,weight=:weight,match_type=:match_type,example=:example,description=:description,is_active=:is_active,updated_at=:now WHERE id=:id"), params)
            else:
                db.execute(text("INSERT INTO nseae_lexicons(id,phrase,indicator,weight,match_type,example,description,is_active,created_by,created_at,updated_at) VALUES (:id,:phrase,:indicator,:weight,:match_type,:example,:description,:is_active,:actor,:now,:now)"), params)
        return next(item for item in self.crud_list("nseae_lexicons") if item["id"] == item_id)

    def test_lexicons(self, sample: str) -> list[dict[str, Any]]:
        matches = []
        for item in self.crud_list("nseae_lexicons"):
            if not item["is_active"]: continue
            phrase, kind = item["phrase"], item["match_type"]
            found = phrase.casefold() == sample.casefold() if kind == "exact" else phrase.casefold() in sample.casefold() if kind == "contains" else bool(re.search(phrase, sample, re.IGNORECASE))
            if found: matches.append({"id": item["id"], "phrase": phrase, "indicator": item["indicator"], "weight": item["weight"]})
        return matches

    def save_recommendation(self, item_id: str | None, payload: dict[str, Any], actor_id: str) -> dict[str, Any]:
        now, item_id = datetime.now(timezone.utc), item_id or str(uuid.uuid4()); params = {**payload, "id": item_id, "actor": actor_id, "now": now}
        with self.engine.begin() as db:
            if db.execute(text("SELECT 1 FROM action_recommendations WHERE id=:id"), {"id": item_id}).first():
                db.execute(text("UPDATE action_recommendations SET title=:title,content=:content,category=:category,risk_level=:risk_level,nseae_indicator=:nseae_indicator,display_order=:display_order,is_active=:is_active,updated_at=:now WHERE id=:id"), params)
            else:
                db.execute(text("INSERT INTO action_recommendations(id,title,content,category,risk_level,nseae_indicator,display_order,is_active,created_by,created_at,updated_at) VALUES (:id,:title,:content,:category,:risk_level,:nseae_indicator,:display_order,:is_active,:actor,:now,:now)"), params)
        return next(item for item in self.crud_list("action_recommendations") if item["id"] == item_id)

    def archive(self, table: str, item_id: str) -> bool:
        if table not in {"nseae_lexicons", "action_recommendations"}: raise ValueError("Tabel tidak diizinkan")
        with self.engine.begin() as db:
            result = db.execute(text(f"UPDATE {table} SET deleted_at=:now,is_active=FALSE WHERE id=:id"), {"id": item_id, "now": datetime.now(timezone.utc)})
        return result.rowcount > 0

    def save_nseae_validation(self, candidate_id: str, rows: list[dict[str, Any]], validator_id: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        with self.engine.begin() as db:
            if not db.execute(text("SELECT 1 FROM dataset_candidates WHERE id=:id AND deleted_at IS NULL"), {"id": candidate_id}).first(): raise ValueError("Kandidat dataset tidak ditemukan.")
            for row in rows:
                if row["indicator"] not in INDICATORS or row["human_validation"] not in {"detected", "not_detected", "unsure"}: raise ValueError("Nilai validasi tidak valid.")
                existing = db.execute(text("SELECT id FROM nseae_validations WHERE dataset_candidate_id=:candidate AND indicator=:indicator"), {"candidate": candidate_id, "indicator": row["indicator"]}).first()
                params = {**row, "id": existing[0] if existing else str(uuid.uuid4()), "candidate": candidate_id, "validator": validator_id, "now": now}
                if existing: db.execute(text("UPDATE nseae_validations SET ai_score=:ai_score,human_validation=:human_validation,detected_evidence=:detected_evidence,validator_id=:validator,notes=:notes,validated_at=:now WHERE id=:id"), params)
                else: db.execute(text("INSERT INTO nseae_validations(id,dataset_candidate_id,indicator,ai_score,human_validation,detected_evidence,validator_id,notes,validated_at) VALUES (:id,:candidate,:indicator,:ai_score,:human_validation,:detected_evidence,:validator,:notes,:now)"), params)
        return [item for item in self.crud_list("nseae_validations") if item["dataset_candidate_id"] == candidate_id]

    def settings(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for item in self.crud_list("system_settings"):
            result.setdefault(item["setting_group"], {})[item["setting_key"]] = item["value"]
        return result

    def setting(self, group: str, key: str, default: str = "") -> str:
        with self.engine.connect() as db:
            value = db.execute(text("SELECT value FROM system_settings WHERE setting_group=:group AND setting_key=:key"), {"group": group, "key": key}).scalar()
        return str(value) if value is not None else default

    def setting_enabled(self, group: str, key: str, default: bool = True) -> bool:
        return self.setting(group, key, "true" if default else "false").casefold() in {"1", "true", "yes", "on", "aktif"}

    def active_lexicons(self) -> list[dict[str, Any]]:
        return [item for item in self.crud_list("nseae_lexicons") if item["is_active"]]

    def recommendation(self, category: str, risk_level: str, indicators: list[str]) -> str | None:
        ranked: list[tuple[int, int, str]] = []
        for item in self.crud_list("action_recommendations"):
            if not item["is_active"] or item.get("category") not in {None, "", category}: continue
            if item.get("risk_level") not in {None, "", risk_level}: continue
            if item.get("nseae_indicator") not in {None, ""} and item["nseae_indicator"] not in indicators: continue
            specificity = sum(bool(item.get(key)) for key in ("category", "risk_level", "nseae_indicator"))
            ranked.append((specificity, -int(item.get("display_order") or 0), item["content"]))
        return max(ranked, default=(0, 0, ""))[2] or None

    def save_settings(self, values: dict[str, dict[str, str]], actor_id: str) -> dict[str, dict[str, Any]]:
        now = datetime.now(timezone.utc)
        with self.engine.begin() as db:
            for group, items in values.items():
                for key, value in items.items():
                    result = db.execute(text("UPDATE system_settings SET value=:value,updated_by=:actor,updated_at=:now WHERE setting_group=:group AND setting_key=:key"), {"value": str(value), "actor": actor_id, "now": now, "group": group, "key": key})
                    if not result.rowcount: db.execute(text("INSERT INTO system_settings(id,setting_group,setting_key,value,value_type,is_public,updated_by,updated_at) VALUES (:id,:group,:key,:value,'string',FALSE,:actor,:now)"), {"id": str(uuid.uuid4()), "group": group, "key": key, "value": str(value), "actor": actor_id, "now": now})
        return self.settings()

    def statistics(self, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        clauses, params = ["1=1"], {}
        if start: clauses.append("analyzed_at>=:start"); params["start"] = start
        if end: clauses.append("analyzed_at<=:end"); params["end"] = f"{end} 23:59:59"
        where = " AND ".join(clauses)
        with self.engine.connect() as db:
            total = int(db.execute(text(f"SELECT COUNT(*) FROM analysis_statistics WHERE {where}"), params).scalar_one())
            successful = int(db.execute(text(f"SELECT COUNT(*) FROM analysis_statistics WHERE {where} AND processing_status='success'"), params).scalar_one())
            avg_response = float(db.execute(text(f"SELECT COALESCE(AVG(response_time_ms),0) FROM analysis_statistics WHERE {where}"), params).scalar_one())
            categories = [dict(row) for row in db.execute(text(f"SELECT category,COUNT(*) AS count FROM analysis_statistics WHERE {where} GROUP BY category ORDER BY count DESC"), params).mappings().all()]
            risks = [dict(row) for row in db.execute(text(f"SELECT risk_level,COUNT(*) AS count FROM analysis_statistics WHERE {where} GROUP BY risk_level ORDER BY count DESC"), params).mappings().all()]
            daily = [dict(row) for row in db.execute(text(f"SELECT substr(CAST(analyzed_at AS VARCHAR),1,10) AS day,COUNT(*) AS count FROM analysis_statistics WHERE {where} GROUP BY substr(CAST(analyzed_at AS VARCHAR),1,10) ORDER BY day"), params).mappings().all()]
            reports = {row["status"]: row["count"] for row in db.execute(text("SELECT status,COUNT(*) AS count FROM reports WHERE deleted_at IS NULL GROUP BY status")).mappings().all()}
            dataset = {row["category"]: row["count"] for row in db.execute(text("SELECT category,COUNT(*) AS count FROM dataset_candidates WHERE is_archived=FALSE AND deleted_at IS NULL GROUP BY category")).mappings().all()}
            splits = {str(row["split"] or "unassigned"): row["count"] for row in db.execute(text("SELECT split,COUNT(*) AS count FROM dataset_candidates WHERE is_archived=FALSE AND deleted_at IS NULL GROUP BY split")).mappings().all()}
            sources = {row["source"]: row["count"] for row in db.execute(text("SELECT source,COUNT(*) AS count FROM dataset_candidates WHERE is_archived=FALSE AND deleted_at IS NULL GROUP BY source")).mappings().all()}
            types = {row["data_type"]: row["count"] for row in db.execute(text("SELECT data_type,COUNT(*) AS count FROM dataset_candidates WHERE is_archived=FALSE AND deleted_at IS NULL GROUP BY data_type")).mappings().all()}
            indicator_counts = {name: 0 for name in INDICATORS}
            for (serialized,) in db.execute(text(f"SELECT detected_indicators FROM analysis_statistics WHERE {where}"), params).all():
                for name in json.loads(serialized or "[]"):
                    if name in indicator_counts: indicator_counts[name] += 1
        return {"total": total, "successful": successful, "failed": total-successful, "average_response_ms": round(avg_response, 2), "categories": categories, "risks": risks, "daily": daily, "reports": reports, "dataset_categories": dataset, "dataset_splits": splits, "dataset_sources": sources, "dataset_types": types, "indicators": indicator_counts}

    def model_versions(self) -> list[dict[str, Any]]:
        return self.crud_list("model_versions")

    def save_model_version(self, payload: dict[str, Any]) -> dict[str, Any]:
        now, item_id = datetime.now(timezone.utc), payload.get("id") or str(uuid.uuid4()); params = {**payload, "id": item_id, "now": now}
        with self.engine.begin() as db:
            if payload.get("status") == "active": db.execute(text("UPDATE model_versions SET status='inactive',updated_at=:now"), {"now": now})
            if db.execute(text("SELECT 1 FROM model_versions WHERE id=:id"), {"id": item_id}).first():
                db.execute(text("UPDATE model_versions SET model_name=:model_name,version=:version,status=:status,accuracy=:accuracy,precision_score=:precision_score,recall_score=:recall_score,f1_score=:f1_score,evaluation_dataset=:evaluation_dataset,evaluated_at=:evaluated_at,notes=:notes,updated_at=:now WHERE id=:id"), params)
            else:
                db.execute(text("INSERT INTO model_versions(id,model_name,version,status,accuracy,precision_score,recall_score,f1_score,evaluation_dataset,evaluated_at,notes,created_at,updated_at) VALUES (:id,:model_name,:version,:status,:accuracy,:precision_score,:recall_score,:f1_score,:evaluation_dataset,:evaluated_at,:notes,:now,:now)"), params)
        return next(item for item in self.model_versions() if item["id"] == item_id)

    def candidate_distribution(self, target: int = 500) -> dict[str, Any]:
        stats = self.statistics()
        categories = [{"category": category, "count": int(stats["dataset_categories"].get(category, 0)), "target": target, "percent": min(round(int(stats["dataset_categories"].get(category, 0))/target*100, 1), 100)} for category in CATEGORIES]
        counts = [item["count"] for item in categories]
        imbalance = bool(counts and max(counts) > max(min(counts), 1) * 1.5)
        return {"categories": categories, "splits": stats["dataset_splits"], "sources": stats["dataset_sources"], "data_types": stats["dataset_types"], "imbalanced": imbalance, "target_per_category": target}

    def save_activity(self, actor: dict[str, Any], action: str, module: str, entity_id: str | None, description: str, old_values: Any = None, new_values: Any = None, ip: str | None = None, agent: str | None = None) -> None:
        ip, agent = ip or request_ip.get(), agent or request_agent.get()
        safe_old = json.dumps(old_values, default=str) if old_values is not None else None; safe_new = json.dumps(new_values, default=str) if new_values is not None else None
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO admin_activity_logs(id,admin_email,action,object_type,object_id,detail,created_at,user_id,module,entity_type,old_values,new_values,ip_address,user_agent) VALUES (:id,:email,:action,:module,:entity,:description,:now,:user,:module,:module,:old,:new,:ip,:agent)"), {"id": str(uuid.uuid4()), "email": actor["email"], "action": action, "module": module, "entity": entity_id, "description": description, "now": datetime.now(timezone.utc), "user": actor["id"], "old": safe_old, "new": safe_new, "ip": ip, "agent": agent})


admin_domain: AdminDomain | None = None


def initialize_admin_domain(store: Any) -> AdminDomain:
    global admin_domain
    if admin_domain is None:
        admin_domain = AdminDomain(store)
    return admin_domain
