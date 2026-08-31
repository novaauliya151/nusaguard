import os
import hashlib
import json
import re
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

DEFAULT_EDUCATION = [
    ("seed-phishing", "Waspada tautan dan APK palsu", "Phishing/Link Berbahaya", "Penipu menyamarkan tautan atau file APK sebagai undangan, paket, dan layanan resmi.", ["Domain asing atau file .apk", "Meminta segera membuka tautan"], ["Buka aplikasi resmi secara mandiri", "Jangan memasang APK dari pesan"]),
    ("seed-social", "Jaga OTP, PIN, dan kata sandi", "Social Engineering", "Pelaku menyamar sebagai petugas untuk meminta kredensial rahasia.", ["Meminta OTP atau PIN", "Mengancam akun akan diblokir"], ["Jangan pernah membagikan kredensial", "Hubungi kanal resmi"]),
    ("seed-investment", "Kenali investasi tidak masuk akal", "Penipuan Investasi", "Janji keuntungan pasti dan tekanan transfer cepat merupakan tanda utama penipuan investasi.", ["Profit pasti tanpa risiko", "Diminta transfer ke rekening pribadi"], ["Periksa izin OJK", "Hindari keputusan karena tekanan"]),
    ("seed-recruitment", "Lowongan resmi tidak meminta biaya", "Penipuan Rekrutmen", "Lowongan palsu sering meminta biaya administrasi, seragam, atau data sensitif sebelum wawancara.", ["Membayar sebelum proses seleksi", "Email bukan domain perusahaan"], ["Verifikasi melalui situs perusahaan", "Jangan membayar proses rekrutmen"]),
    ("seed-romance", "Waspada manipulasi hubungan daring", "Penipuan Romansa", "Pelaku membangun kedekatan lalu menciptakan keadaan darurat untuk meminta uang.", ["Belum pernah bertemu", "Berulang kali meminta bantuan uang"], ["Verifikasi identitas", "Diskusikan dengan orang tepercaya"]),
    ("seed-safe", "Ciri pesan yang lebih aman", "Aman", "Pesan edukasi mengingatkan pengguna agar tidak membagikan data dan mengarahkan ke kanal resmi tanpa tekanan.", ["Tidak meminta kredensial", "Tidak menyuruh membuka tautan asing"], ["Tetap verifikasi pengirim", "Gunakan aplikasi resmi"]),
]

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
            db.execute(text("CREATE TABLE IF NOT EXISTS dataset_candidates (id VARCHAR(36) PRIMARY KEY, report_id VARCHAR(36), text_anonymized TEXT NOT NULL, category VARCHAR(80) NOT NULL, source VARCHAR(50) NOT NULL DEFAULT 'community_report', data_type VARCHAR(20) NOT NULL DEFAULT 'primer', validation_status VARCHAR(20) NOT NULL DEFAULT 'pending', split VARCHAR(20), validator VARCHAR(160), notes TEXT, is_duplicate BOOLEAN NOT NULL DEFAULT FALSE, is_archived BOOLEAN NOT NULL DEFAULT FALSE, nseae_validation TEXT NOT NULL DEFAULT '{}', created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS admin_activity_logs (id VARCHAR(36) PRIMARY KEY, admin_email VARCHAR(160) NOT NULL, action VARCHAR(80) NOT NULL, object_type VARCHAR(50) NOT NULL, object_id VARCHAR(36), detail TEXT, created_at TIMESTAMP NOT NULL)"))
            columns = {row[1] for row in db.execute(text("PRAGMA table_info(reports)"))} if url.startswith("sqlite") else set()
            if columns and "status" not in columns:
                db.execute(text("ALTER TABLE reports ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'"))
            if columns:
                report_columns = {row[1] for row in db.execute(text("PRAGMA table_info(reports)"))}
                additions = {"source":"VARCHAR(50)","additional_notes":"TEXT","correct_category":"VARCHAR(80)","validation_notes":"TEXT","is_duplicate":"BOOLEAN NOT NULL DEFAULT FALSE","admin_result":"TEXT"}
                for column, definition in additions.items():
                    if column not in report_columns: db.execute(text(f"ALTER TABLE reports ADD COLUMN {column} {definition}"))
            elif url.startswith("postgresql"):
                additions = {"source":"VARCHAR(50)","additional_notes":"TEXT","correct_category":"VARCHAR(80)","validation_notes":"TEXT","is_duplicate":"BOOLEAN NOT NULL DEFAULT FALSE","admin_result":"TEXT"}
                for column, definition in additions.items(): db.execute(text(f"ALTER TABLE reports ADD COLUMN IF NOT EXISTS {column} {definition}"))
            now = datetime.now(timezone.utc)
            for item_id, title, category, description, signs, prevention in DEFAULT_EDUCATION:
                db.execute(text("INSERT INTO education_items(id,title,category,description,warning_signs,prevention,is_published,created_at,updated_at) SELECT :id,:title,:category,:description,:signs,:prevention,TRUE,:now,:now WHERE NOT EXISTS (SELECT 1 FROM education_items WHERE id=:id)"), {"id":item_id,"title":title,"category":category,"description":description,"signs":json.dumps(signs),"prevention":json.dumps(prevention),"now":now})
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
    def report(self, content: str, category: str, source: str | None = None, additional_notes: str | None = None, user_id: str | None = None, anonymized_text: str | None = None) -> tuple[str, datetime]:
        report_id, created = str(uuid.uuid4()), datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO reports(id,text,anonymized_text,category_suggested,source,additional_notes,user_id,created_at,updated_at) VALUES (:id,:content,:anonymized,:category,:source,:notes,:user,:created,:created)"), {"id":report_id,"content":content,"anonymized":anonymized_text,"category":category,"source":source,"notes":additional_notes,"user":user_id,"created":created})
        return report_id, created

    def admin_dashboard(self, limit: int = 100) -> dict:
        total, counts = self.stats()
        with self.engine.connect() as db:
            reports_total = db.execute(text("SELECT COUNT(*) FROM reports")).scalar_one()
            reports_pending = db.execute(text("SELECT COUNT(*) FROM reports WHERE status='pending'")).scalar_one()
            rows = db.execute(text("SELECT id,text,category_suggested,status,created_at FROM reports ORDER BY created_at DESC LIMIT :limit"), {"limit": limit}).mappings().all()
            daily = db.execute(text("SELECT day,SUM(count) AS count FROM stats_daily GROUP BY day ORDER BY day DESC LIMIT 14")).mappings().all()
            sources = db.execute(text("SELECT source,SUM(count) AS count FROM stats_daily GROUP BY source ORDER BY count DESC")).mappings().all()
            reports_reviewed = db.execute(text("SELECT COUNT(*) FROM reports WHERE status IN ('reviewed','approved','dataset_candidate')")).scalar_one()
            candidates_total = db.execute(text("SELECT COUNT(*) FROM dataset_candidates WHERE is_archived=FALSE")).scalar_one()
            education_published = db.execute(text("SELECT COUNT(*) FROM education_items WHERE is_published=TRUE")).scalar_one()
            today = datetime.now(timezone.utc).date().isoformat()
            month = today[:7]
            today_total = db.execute(text("SELECT COALESCE(SUM(count),0) FROM stats_daily WHERE day=:day"), {"day":today}).scalar_one()
            month_total = db.execute(text("SELECT COALESCE(SUM(count),0) FROM stats_daily WHERE day LIKE :month"), {"month":f"{month}%"}).scalar_one()
        return {
            "total": total, "counts": counts, "reports_total": reports_total,
            "reports_pending": reports_pending, "reports": [dict(row) for row in rows],
            "daily": list(reversed([dict(row) for row in daily])),
            "sources": {row["source"]: row["count"] for row in sources},
            "database_engine": self.engine.url.get_backend_name(),
            "reports_reviewed": reports_reviewed, "candidates_total": candidates_total,
            "education_published": education_published, "today_total": today_total, "month_total": month_total,
        }

    def update_report_status(self, report_id: str, status: str) -> bool:
        with self.lock, self.engine.begin() as db:
            result = db.execute(text("UPDATE reports SET status=:status WHERE id=:id"), {"status": status, "id": report_id})
        return result.rowcount > 0

    def validate_report(self, report_id: str, payload: dict) -> dict | None:
        fields={key:value for key,value in payload.items() if value is not None}
        if not fields:return self.get_report(report_id)
        fields["id"]=report_id
        with self.lock,self.engine.begin() as db:
            result=db.execute(text("UPDATE reports SET "+",".join(f"{key}=:{key}" for key in fields if key!="id")+" WHERE id=:id"),fields)
        return self.get_report(report_id) if result.rowcount else None

    def get_report(self, report_id: str) -> dict | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT * FROM reports WHERE id=:id"), {"id":report_id}).mappings().first()
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
            row = db.execute(text("SELECT id,name,email,role,is_active,status,avatar,must_change_password,last_login_at,created_by,created_at,updated_at,deleted_at FROM users WHERE id=:id AND deleted_at IS NULL"), {"id":user_id}).mappings().first()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> dict | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT id,name,email,role,is_active,status,avatar,must_change_password,last_login_at,created_by,created_at,updated_at,deleted_at FROM users WHERE email=:email AND deleted_at IS NULL"), {"email": email.casefold()}).mappings().first()
        return dict(row) if row else None

    def authenticate(self, email: str, password: str, remember_me: bool = False) -> tuple[str, dict] | None:
        with self.engine.connect() as db:
            row = db.execute(text("SELECT * FROM users WHERE email=:email"), {"email":email.casefold()}).mappings().first()
        if not row or row.get("deleted_at") or not row["is_active"] or row.get("status", "active") != "active" or not self._password_valid(password, row["password_hash"]):
            return None
        token, now = secrets.token_urlsafe(32), datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO user_sessions(token_hash,user_id,expires_at,created_at) VALUES (:token,:user,:expires,:created)"), {"token":hashlib.sha256(token.encode()).hexdigest(),"user":row["id"],"expires":now+timedelta(days=30 if remember_me else 1),"created":now})
            db.execute(text("UPDATE users SET last_login_at=:now,updated_at=:now WHERE id=:id"), {"now": now, "id": row["id"]})
        return token, self.get_user(row["id"])

    def user_from_token(self, token: str) -> dict | None:
        digest, now = hashlib.sha256(token.encode()).hexdigest(), datetime.now(timezone.utc)
        with self.engine.connect() as db:
            row = db.execute(text("SELECT u.id,u.name,u.email,u.role,u.is_active,u.status,u.avatar,u.must_change_password,u.last_login_at,u.created_by,u.created_at,u.updated_at,u.deleted_at FROM user_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=:token AND s.expires_at>:now AND u.is_active=TRUE AND u.status='active' AND u.deleted_at IS NULL"), {"token":digest,"now":now}).mappings().first()
        return dict(row) if row else None

    def list_users(self) -> list[dict]:
        with self.engine.connect() as db:
            rows = db.execute(text("SELECT id,name,email,role,is_active,created_at FROM users ORDER BY created_at DESC")).mappings().all()
        return [dict(row) for row in rows]

    def update_user(self, user_id: str, role: str | None, is_active: bool | None, name: str | None = None, email: str | None = None, password: str | None = None) -> dict | None:
        updates, params = [], {"id":user_id}
        if name is not None: updates.append("name=:name"); params["name"] = name
        if email is not None: updates.append("email=:email"); params["email"] = email.casefold()
        if password is not None: updates.append("password_hash=:password"); params["password"] = self._password_hash(password)
        if role is not None: updates.append("role=:role"); params["role"] = role
        if is_active is not None: updates.append("is_active=:active"); params["active"] = is_active
        if not updates: return self.get_user(user_id)
        with self.lock, self.engine.begin() as db:
            db.execute(text(f"UPDATE users SET {','.join(updates)} WHERE id=:id"), params)
            if is_active is False: db.execute(text("DELETE FROM user_sessions WHERE user_id=:id"), {"id":user_id})
        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> bool:
        with self.lock, self.engine.begin() as db:
            db.execute(text("DELETE FROM user_sessions WHERE user_id=:id"), {"id": user_id})
            result = db.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})
        return result.rowcount > 0

    def education(self, published_only: bool = True) -> list[dict]:
        clause = " WHERE is_published=TRUE AND deleted_at IS NULL" if published_only else " WHERE deleted_at IS NULL"
        with self.engine.connect() as db:
            rows = db.execute(text(f"SELECT * FROM education_items{clause} ORDER BY updated_at DESC")).mappings().all()
        return [{**dict(row), "warning_signs": json.loads(row["warning_signs"]), "prevention": json.loads(row["prevention"]), "response_steps": json.loads(row.get("response_steps") or "[]")} for row in rows]

    def save_education(self, item_id: str | None, payload: dict) -> dict:
        now, item_id = datetime.now(timezone.utc), item_id or str(uuid.uuid4())
        supplied_slug = payload.get("slug")
        slug = supplied_slug or "-".join(re.findall(r"[a-z0-9]+", payload["title"].casefold()))
        params = {**payload, "slug":slug, "warning_signs":json.dumps(payload["warning_signs"]), "prevention":json.dumps(payload["prevention"]), "response_steps":json.dumps(payload.get("response_steps", [])), "published_at":payload.get("published_at") or (now if payload.get("status")=="published" else None), "id": item_id, "created": now, "updated": now}
        with self.lock, self.engine.begin() as db:
            if db.execute(text("SELECT id FROM education_items WHERE slug=:slug AND id<>:id AND deleted_at IS NULL"), {"slug":slug,"id":item_id}).first():
                if supplied_slug: raise ValueError("Slug konten sudah digunakan.")
                slug=f"{slug}-{item_id[:8]}";params["slug"]=slug
            exists = db.execute(text("SELECT id FROM education_items WHERE id=:id"), {"id":item_id}).first()
            if exists:
                db.execute(text("UPDATE education_items SET title=:title,slug=:slug,category=:category,description=:description,summary=:summary,content=:content,warning_signs=:warning_signs,anonymized_example=:anonymized_example,prevention=:prevention,response_steps=:response_steps,thumbnail=:thumbnail,image_alt=:image_alt,meta_title=:meta_title,meta_description=:meta_description,status=:status,published_at=:published_at,display_order=:display_order,is_published=:is_published,updated_at=:updated WHERE id=:id"), params)
            else:
                db.execute(text("INSERT INTO education_items(id,title,slug,category,description,summary,content,warning_signs,anonymized_example,prevention,response_steps,thumbnail,image_alt,meta_title,meta_description,status,published_at,display_order,is_published,created_at,updated_at) VALUES (:id,:title,:slug,:category,:description,:summary,:content,:warning_signs,:anonymized_example,:prevention,:response_steps,:thumbnail,:image_alt,:meta_title,:meta_description,:status,:published_at,:display_order,:is_published,:created,:updated)"), params)
        return next(row for row in self.education(False) if row["id"] == item_id)

    def delete_education(self, item_id: str) -> bool:
        with self.lock, self.engine.begin() as db:
            result = db.execute(text("UPDATE education_items SET deleted_at=:now,is_published=FALSE,status='archived',updated_at=:now WHERE id=:id"), {"id":item_id,"now":datetime.now(timezone.utc)})
        return result.rowcount > 0

    def publish_report_dataset(self, report_id: str, anonymized: str) -> dict | None:
        now = datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            report = db.execute(text("SELECT category_suggested FROM reports WHERE id=:id AND status IN ('reviewed','approved')"), {"id":report_id}).mappings().first()
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

    def candidates(self) -> list[dict]:
        with self.engine.connect() as db: rows=db.execute(text("SELECT * FROM dataset_candidates WHERE is_archived=FALSE ORDER BY created_at DESC")).mappings().all()
        return [{**dict(row),"nseae_validation":json.loads(row["nseae_validation"] or "{}")} for row in rows]

    def save_candidate(self, candidate_id: str | None, payload: dict) -> dict:
        now=datetime.now(timezone.utc);candidate_id=candidate_id or str(uuid.uuid4());data={**payload,"id":candidate_id,"created":now,"updated":now,"nseae_validation":json.dumps(payload.get("nseae_validation",{}))}
        with self.lock,self.engine.begin() as db:
            exists=db.execute(text("SELECT id FROM dataset_candidates WHERE id=:id"),{"id":candidate_id}).first()
            if exists: db.execute(text("UPDATE dataset_candidates SET text_anonymized=:text_anonymized,category=:category,source=:source,data_type=:data_type,validation_status=:validation_status,split=:split,validator=:validator,notes=:notes,is_duplicate=:is_duplicate,is_archived=:is_archived,nseae_validation=:nseae_validation,updated_at=:updated WHERE id=:id"),data)
            else: db.execute(text("INSERT INTO dataset_candidates(id,report_id,text_anonymized,category,source,data_type,validation_status,split,validator,notes,is_duplicate,is_archived,nseae_validation,created_at,updated_at) VALUES(:id,:report_id,:text_anonymized,:category,:source,:data_type,:validation_status,:split,:validator,:notes,:is_duplicate,:is_archived,:nseae_validation,:created,:updated)"),data)
        return next(row for row in self.candidates() if row["id"]==candidate_id)

    def archive_candidate(self,candidate_id:str)->bool:
        with self.lock,self.engine.begin() as db: result=db.execute(text("UPDATE dataset_candidates SET is_archived=TRUE,updated_at=:now WHERE id=:id"),{"id":candidate_id,"now":datetime.now(timezone.utc)})
        return result.rowcount>0

    def add_activity(self,admin_email:str,action:str,object_type:str,object_id:str|None=None,detail:str|None=None)->None:
        with self.lock,self.engine.begin() as db: db.execute(text("INSERT INTO admin_activity_logs(id,admin_email,action,object_type,object_id,detail,created_at) VALUES(:id,:admin,:action,:type,:object,:detail,:created)"),{"id":str(uuid.uuid4()),"admin":admin_email,"action":action,"type":object_type,"object":object_id,"detail":detail,"created":datetime.now(timezone.utc)})

    def activities(self,limit:int=100)->list[dict]:
        with self.engine.connect() as db: rows=db.execute(text("SELECT * FROM admin_activity_logs ORDER BY created_at DESC LIMIT :limit"),{"limit":limit}).mappings().all()
        return [dict(row) for row in rows]

    def change_password(self,user_id:str,current_password:str,new_password:str)->bool:
        with self.engine.connect() as db: row=db.execute(text("SELECT password_hash FROM users WHERE id=:id"),{"id":user_id}).mappings().first()
        if not row or not self._password_valid(current_password,row["password_hash"]):return False
        with self.lock,self.engine.begin() as db: db.execute(text("UPDATE users SET password_hash=:password,must_change_password=FALSE,updated_at=:now WHERE id=:id"),{"password":self._password_hash(new_password),"id":user_id,"now":datetime.now(timezone.utc)})
        return True

    def revoke_token(self, token: str) -> bool:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.lock, self.engine.begin() as db:
            result = db.execute(text("DELETE FROM user_sessions WHERE token_hash=:token"), {"token": digest})
        return result.rowcount > 0

store = Store()

# Schema admin diletakkan terpisah agar instalasi lama dapat dimigrasikan tanpa
# mengganti Store dan DATABASE_URL yang sudah digunakan aplikasi.
from app.services.admin_domain import initialize_admin_domain

admin_domain = initialize_admin_domain(store)

from app.services.user_domain import initialize_user_domain

user_domain = initialize_user_domain(store)

