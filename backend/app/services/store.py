import os
import hashlib
import json
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

class Store:
    def __init__(self) -> None:
        url = os.getenv("DATABASE_URL", "sqlite:///nusaguard.db").replace("postgres://", "postgresql+psycopg://", 1)
        self.engine, self.lock = create_engine(url, pool_pre_ping=True), threading.Lock()
        with self.engine.begin() as db:
            db.execute(text("CREATE TABLE IF NOT EXISTS reports (id VARCHAR(36) PRIMARY KEY, text TEXT NOT NULL, category_suggested VARCHAR(80) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'pending', created_at TIMESTAMP NOT NULL)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS stats (category VARCHAR(80) PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS stats_daily (day VARCHAR(10) NOT NULL, category VARCHAR(80) NOT NULL, source VARCHAR(30) NOT NULL, count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(day,category,source))"))
            db.execute(text("CREATE TABLE IF NOT EXISTS users (id VARCHAR(36) PRIMARY KEY, name VARCHAR(80) NOT NULL, email VARCHAR(160) NOT NULL UNIQUE, password_hash VARCHAR(256) NOT NULL, role VARCHAR(20) NOT NULL DEFAULT 'user', is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS user_sessions (token_hash VARCHAR(64) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, expires_at TIMESTAMP NOT NULL, created_at TIMESTAMP NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id))"))
            db.execute(text("CREATE TABLE IF NOT EXISTS education_items (id VARCHAR(36) PRIMARY KEY, title VARCHAR(120) NOT NULL, category VARCHAR(80) NOT NULL, description TEXT NOT NULL, warning_signs TEXT NOT NULL, prevention TEXT NOT NULL, is_published BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS public_dataset (id VARCHAR(36) PRIMARY KEY, report_id VARCHAR(36) NOT NULL UNIQUE, text_anonymized TEXT NOT NULL, category VARCHAR(80) NOT NULL, provenance VARCHAR(50) NOT NULL, reviewed BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL, FOREIGN KEY(report_id) REFERENCES reports(id))"))
            columns = {row[1] for row in db.execute(text("PRAGMA table_info(reports)"))} if url.startswith("sqlite") else set()
            if columns and "status" not in columns:
                db.execute(text("ALTER TABLE reports ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'"))
    def increment(self, category: str, source: str = "unknown") -> None:
        day = datetime.now(timezone.utc).date().isoformat()
        safe_source = source[:30] if source else "unknown"
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO stats(category,count) VALUES (:category,1) ON CONFLICT(category) DO UPDATE SET count=stats.count+1"), {"category":category})
            db.execute(text("INSERT INTO stats_daily(day,category,source,count) VALUES (:day,:category,:source,1) ON CONFLICT(day,category,source) DO UPDATE SET count=stats_daily.count+1"), {"day": day, "category": category, "source": safe_source})
    def stats(self) -> tuple[int, dict[str, int]]:
        with self.engine.connect() as db:
            counts={row.category:row.count for row in db.execute(text("SELECT category,count FROM stats"))}
        return sum(counts.values()), counts
    def public_statistics(self) -> dict:
        total, counts = self.stats()
        month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
        with self.engine.connect() as db:
            month_rows = db.execute(text("SELECT category,SUM(count) AS count FROM stats_daily WHERE day LIKE :month GROUP BY category ORDER BY count DESC"), {"month": f"{month_prefix}%"}).mappings().all()
            daily_rows = db.execute(text("SELECT day,SUM(count) AS count FROM stats_daily GROUP BY day ORDER BY day DESC LIMIT 14")).mappings().all()
        month_counts = {row["category"]: row["count"] for row in month_rows}
        return {"total": total, "counts": counts, "month_total": sum(month_counts.values()), "month_counts": month_counts, "top_category": month_rows[0]["category"] if month_rows else None, "daily": list(reversed([dict(row) for row in daily_rows])), "updated_at": datetime.now(timezone.utc)}
    def report(self, content: str, category: str) -> tuple[str, datetime]:
        report_id, created = str(uuid.uuid4()), datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO reports(id,text,category_suggested,created_at) VALUES (:id,:content,:category,:created)"), {"id":report_id,"content":content,"category":category,"created":created})
        return report_id, created

    def admin_dashboard(self, limit: int = 100) -> dict:
        total, counts = self.stats()
        with self.engine.connect() as db:
            reports_total = db.execute(text("SELECT COUNT(*) FROM reports")).scalar_one()
            reports_pending = db.execute(text("SELECT COUNT(*) FROM reports WHERE status='pending'")).scalar_one()
            rows = db.execute(text("SELECT id,text,category_suggested,status,created_at FROM reports ORDER BY created_at DESC LIMIT :limit"), {"limit": limit}).mappings().all()
            daily = db.execute(text("SELECT day,SUM(count) AS count FROM stats_daily GROUP BY day ORDER BY day DESC LIMIT 14")).mappings().all()
            sources = db.execute(text("SELECT source,SUM(count) AS count FROM stats_daily GROUP BY source ORDER BY count DESC")).mappings().all()
        return {
            "total": total, "counts": counts, "reports_total": reports_total,
            "reports_pending": reports_pending, "reports": [dict(row) for row in rows],
            "daily": list(reversed([dict(row) for row in daily])),
            "sources": {row["source"]: row["count"] for row in sources},
            "database_engine": self.engine.url.get_backend_name(),
        }

    def update_report_status(self, report_id: str, status: str) -> bool:
        with self.lock, self.engine.begin() as db:
            result = db.execute(text("UPDATE reports SET status=:status WHERE id=:id"), {"status": status, "id": report_id})
        return result.rowcount > 0

    def get_report(self, report_id: str) -> dict | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT id,text,category_suggested,status,created_at FROM reports WHERE id=:id"), {"id":report_id}).mappings().first()
        return dict(row) if row else None

    @staticmethod
    def _password_hash(password: str, salt: str | None = None) -> str:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000).hex()
        return f"pbkdf2_sha256${salt}${digest}"

    @classmethod
    def _password_valid(cls, password: str, encoded: str) -> bool:
        try:
            _, salt, _ = encoded.split("$", 2)
            return secrets.compare_digest(cls._password_hash(password, salt), encoded)
        except ValueError:
            return False

    def create_user(self, name: str, email: str, password: str, role: str = "user") -> dict | None:
        user_id, created = str(uuid.uuid4()), datetime.now(timezone.utc)
        try:
            with self.lock, self.engine.begin() as db:
                db.execute(text("INSERT INTO users(id,name,email,password_hash,role,is_active,created_at) VALUES (:id,:name,:email,:password,:role,:active,:created)"), {"id":user_id,"name":name,"email":email.casefold(),"password":self._password_hash(password),"role":role,"active":True,"created":created})
        except Exception as exc:
            if "unique" in str(exc).casefold() or "duplicate" in str(exc).casefold():
                return None
            raise
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> dict | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT id,name,email,role,is_active,created_at FROM users WHERE id=:id"), {"id":user_id}).mappings().first()
        return dict(row) if row else None

    def authenticate(self, email: str, password: str) -> tuple[str, dict] | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT * FROM users WHERE email=:email"), {"email":email.casefold()}).mappings().first()
        if not row or not row["is_active"] or not self._password_valid(password, row["password_hash"]):
            return None
        token, now = secrets.token_urlsafe(32), datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO user_sessions(token_hash,user_id,expires_at,created_at) VALUES (:token,:user,:expires,:created)"), {"token":hashlib.sha256(token.encode()).hexdigest(),"user":row["id"],"expires":now+timedelta(days=7),"created":now})
        return token, self.get_user(row["id"])

    def user_from_token(self, token: str) -> dict | None:
        digest, now = hashlib.sha256(token.encode()).hexdigest(), datetime.now(timezone.utc)
        with self.engine.connect() as db:
            row = db.execute(text("SELECT u.id,u.name,u.email,u.role,u.is_active,u.created_at FROM user_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=:token AND s.expires_at>:now AND u.is_active=TRUE"), {"token":digest,"now":now}).mappings().first()
        return dict(row) if row else None

    def list_users(self) -> list[dict]:
        with self.engine.connect() as db:
            rows = db.execute(text("SELECT id,name,email,role,is_active,created_at FROM users ORDER BY created_at DESC")).mappings().all()
        return [dict(row) for row in rows]

    def update_user(self, user_id: str, role: str | None, is_active: bool | None) -> dict | None:
        updates, params = [], {"id":user_id}
        if role is not None: updates.append("role=:role"); params["role"] = role
        if is_active is not None: updates.append("is_active=:active"); params["active"] = is_active
        if not updates: return self.get_user(user_id)
        with self.lock, self.engine.begin() as db:
            db.execute(text(f"UPDATE users SET {','.join(updates)} WHERE id=:id"), params)
            if is_active is False: db.execute(text("DELETE FROM user_sessions WHERE user_id=:id"), {"id":user_id})
        return self.get_user(user_id)

    def education(self, published_only: bool = True) -> list[dict]:
        clause = " WHERE is_published=TRUE" if published_only else ""
        with self.engine.connect() as db:
            rows = db.execute(text(f"SELECT * FROM education_items{clause} ORDER BY updated_at DESC")).mappings().all()
        return [{**dict(row), "warning_signs": json.loads(row["warning_signs"]), "prevention": json.loads(row["prevention"])} for row in rows]

    def save_education(self, item_id: str | None, payload: dict) -> dict:
        now, item_id = datetime.now(timezone.utc), item_id or str(uuid.uuid4())
        params = {**payload, "warning_signs":json.dumps(payload["warning_signs"]), "prevention":json.dumps(payload["prevention"]), "id": item_id, "created": now, "updated": now}
        with self.lock, self.engine.begin() as db:
            exists = db.execute(text("SELECT id FROM education_items WHERE id=:id"), {"id":item_id}).first()
            if exists:
                db.execute(text("UPDATE education_items SET title=:title,category=:category,description=:description,warning_signs=:warning_signs,prevention=:prevention,is_published=:is_published,updated_at=:updated WHERE id=:id"), params)
            else:
                db.execute(text("INSERT INTO education_items(id,title,category,description,warning_signs,prevention,is_published,created_at,updated_at) VALUES (:id,:title,:category,:description,:warning_signs,:prevention,:is_published,:created,:updated)"), params)
        return next(row for row in self.education(False) if row["id"] == item_id)

    def delete_education(self, item_id: str) -> bool:
        with self.lock, self.engine.begin() as db:
            result = db.execute(text("DELETE FROM education_items WHERE id=:id"), {"id":item_id})
        return result.rowcount > 0

    def publish_report_dataset(self, report_id: str, anonymized: str) -> dict | None:
        now = datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            report = db.execute(text("SELECT category_suggested FROM reports WHERE id=:id AND status='reviewed'"), {"id":report_id}).mappings().first()
            if not report: return None
            existing = db.execute(text("SELECT id FROM public_dataset WHERE report_id=:id"), {"id":report_id}).first()
            if not existing:
                db.execute(text("INSERT INTO public_dataset(id,report_id,text_anonymized,category,provenance,reviewed,created_at) VALUES (:dataset_id,:report_id,:content,:category,'consented_user_report',TRUE,:created)"), {"dataset_id":str(uuid.uuid4()),"report_id":report_id,"content":anonymized,"category":report["category_suggested"],"created":now})
        return self.dataset_by_report(report_id)

    def dataset_by_report(self, report_id: str) -> dict | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT id,text_anonymized,category,provenance,reviewed,created_at FROM public_dataset WHERE report_id=:id"), {"id":report_id}).mappings().first()
        return dict(row) if row else None

    def public_dataset(self) -> list[dict]:
        with self.engine.connect() as db:
            rows = db.execute(text("SELECT id,text_anonymized,category,provenance,reviewed,created_at FROM public_dataset ORDER BY created_at DESC")).mappings().all()
        return [dict(row) for row in rows]

store = Store()

