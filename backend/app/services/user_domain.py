"""Data pribadi pengguna; semua query selalu dibatasi user_id dari sesi."""
from __future__ import annotations

import json
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text


SENSITIVE = [
    (r"\b\d{6}\b", "[KODE]"),
    (r"\b(?:\d[ -]?){12,19}\b", "[NOMOR_SENSITIF]"),
    (r"\b(?:\+62|62|0)8\d{8,12}\b", "[TELEPON]"),
    (r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[EMAIL]"),
    (r"(?i)\b(?:otp|pin|password|kata sandi|token)\s*[:=]?\s*\S+", "[KREDENSIAL]"),
]


def anonymize_user_text(value: str) -> str:
    result = value.strip()
    for pattern, replacement in SENSITIVE:
        result = re.sub(pattern, replacement, result)
    return result[:5000]


class UserDomain:
    def __init__(self, store):
        self.store, self.engine = store, store.engine
        self.initialize()

    def initialize(self) -> None:
        ddl = [
            "CREATE TABLE IF NOT EXISTS user_analysis_histories (id VARCHAR(36) PRIMARY KEY,user_id VARCHAR(36) NOT NULL,safe_title VARCHAR(180) NOT NULL,anonymized_text TEXT,category VARCHAR(80) NOT NULL,risk_level VARCHAR(20) NOT NULL,risk_score FLOAT NOT NULL,confidence_score FLOAT,summary TEXT NOT NULL,explanation TEXT NOT NULL,warning_signs TEXT NOT NULL,recommendations TEXT NOT NULL,model_version VARCHAR(80),processing_time_ms FLOAT,is_favorite BOOLEAN NOT NULL DEFAULT FALSE,personal_note TEXT,retention_expires_at TIMESTAMP,parent_history_id VARCHAR(36),created_at TIMESTAMP NOT NULL,updated_at TIMESTAMP NOT NULL,deleted_at TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id))",
            "CREATE TABLE IF NOT EXISTS user_analysis_indicators (id VARCHAR(36) PRIMARY KEY,analysis_history_id VARCHAR(36) NOT NULL,indicator VARCHAR(40) NOT NULL,score FLOAT NOT NULL,detected BOOLEAN NOT NULL,anonymized_evidence TEXT,explanation TEXT,created_at TIMESTAMP NOT NULL,FOREIGN KEY(analysis_history_id) REFERENCES user_analysis_histories(id))",
            "CREATE TABLE IF NOT EXISTS user_privacy_settings (id VARCHAR(36) PRIMARY KEY,user_id VARCHAR(36) NOT NULL UNIQUE,history_storage_mode VARCHAR(20) NOT NULL DEFAULT 'ask',retention_period VARCHAR(20) NOT NULL DEFAULT '90_days',save_anonymized_text BOOLEAN NOT NULL DEFAULT TRUE,require_save_confirmation BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMP NOT NULL,updated_at TIMESTAMP NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id))",
            "CREATE TABLE IF NOT EXISTS user_saved_guides (id VARCHAR(36) PRIMARY KEY,user_id VARCHAR(36) NOT NULL,education_content_id VARCHAR(36) NOT NULL,created_at TIMESTAMP NOT NULL,UNIQUE(user_id,education_content_id))",
            "CREATE TABLE IF NOT EXISTS user_notifications (id VARCHAR(36) PRIMARY KEY,user_id VARCHAR(36) NOT NULL,type VARCHAR(40) NOT NULL,title VARCHAR(160) NOT NULL,message TEXT NOT NULL,action_url TEXT,read_at TIMESTAMP,created_at TIMESTAMP NOT NULL)",
            "CREATE TABLE IF NOT EXISTS password_reset_tokens (token_hash VARCHAR(64) PRIMARY KEY,user_id VARCHAR(36) NOT NULL,expires_at TIMESTAMP NOT NULL,used_at TIMESTAMP,created_at TIMESTAMP NOT NULL)",
        ]
        with self.engine.begin() as db:
            for statement in ddl: db.execute(text(statement))
            self._add_columns(db, "users", {"email_verified_at":"TIMESTAMP"})
            self._add_columns(db, "reports", {"user_id":"VARCHAR(36)","user_hidden_at":"TIMESTAMP"})
            for statement in [
                "CREATE INDEX IF NOT EXISTS idx_history_user ON user_analysis_histories(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_history_created ON user_analysis_histories(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_history_category ON user_analysis_histories(category)",
                "CREATE INDEX IF NOT EXISTS idx_history_risk ON user_analysis_histories(risk_level)",
                "CREATE INDEX IF NOT EXISTS idx_history_favorite ON user_analysis_histories(is_favorite)",
                "CREATE INDEX IF NOT EXISTS idx_history_retention ON user_analysis_histories(retention_expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id)",
            ]: db.execute(text(statement))

    def _add_columns(self, db, table: str, additions: dict[str,str]) -> None:
        backend = self.engine.url.get_backend_name()
        if backend == "sqlite":
            existing = {row[1] for row in db.execute(text(f"PRAGMA table_info({table})"))}
            for name, definition in additions.items():
                if name not in existing: db.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        else:
            for name, definition in additions.items(): db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {definition}"))

    def privacy(self, user_id: str) -> dict:
        now = datetime.now(timezone.utc)
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO user_privacy_settings(id,user_id,created_at,updated_at) SELECT :id,:user,:now,:now WHERE NOT EXISTS(SELECT 1 FROM user_privacy_settings WHERE user_id=:user)"),{"id":str(uuid.uuid4()),"user":user_id,"now":now})
            row=db.execute(text("SELECT * FROM user_privacy_settings WHERE user_id=:user"),{"user":user_id}).mappings().one()
        return dict(row)

    def update_privacy(self,user_id:str,payload:dict)->dict:
        self.privacy(user_id); allowed={"history_storage_mode","retention_period","save_anonymized_text","require_save_confirmation"}; values={k:v for k,v in payload.items() if k in allowed}
        if values:
            values.update(user=user_id,now=datetime.now(timezone.utc))
            with self.engine.begin() as db: db.execute(text("UPDATE user_privacy_settings SET "+",".join(f"{k}=:{k}" for k in values if k not in {'user','now'})+",updated_at=:now WHERE user_id=:user"),values)
        return self.privacy(user_id)

    def save_history(self,user_id:str,payload:dict)->dict:
        settings=self.privacy(user_id)
        if settings["history_storage_mode"]=="never": raise ValueError("Pengaturan privasi menonaktifkan penyimpanan riwayat.")
        now=datetime.now(timezone.utc); history_id=str(uuid.uuid4()); category=payload["category"]
        periods={"30_days":30,"90_days":90,"1_year":365,"forever":None}; days=periods.get(settings["retention_period"],90)
        anonymized=anonymize_user_text(payload.get("text") or "") if settings["save_anonymized_text"] and payload.get("save_text",True) else None
        params={"id":history_id,"user":user_id,"title":f"Analisis {category} — {now.strftime('%d %B %Y')}","text":anonymized,"category":category,"risk":payload["risk_level"],"score":payload["risk_score"],"confidence":payload.get("confidence"),"summary":payload.get("summary") or f"Hasil analisis kategori {category} dengan risiko {payload['risk_level']}.","explanation":json.dumps(payload.get("explanation",[]),ensure_ascii=False),"signs":json.dumps(payload.get("warning_signs",[]),ensure_ascii=False),"recommendations":json.dumps(payload.get("recommendations",[]),ensure_ascii=False),"model":payload.get("model_version"),"processing":payload.get("processing_time_ms"),"expires":now+timedelta(days=days) if days else None,"parent":payload.get("parent_history_id"),"now":now}
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO user_analysis_histories(id,user_id,safe_title,anonymized_text,category,risk_level,risk_score,confidence_score,summary,explanation,warning_signs,recommendations,model_version,processing_time_ms,retention_expires_at,parent_history_id,created_at,updated_at) VALUES(:id,:user,:title,:text,:category,:risk,:score,:confidence,:summary,:explanation,:signs,:recommendations,:model,:processing,:expires,:parent,:now,:now)"),params)
            for name,score in (payload.get("nseae_scores") or {}).items(): db.execute(text("INSERT INTO user_analysis_indicators(id,analysis_history_id,indicator,score,detected,anonymized_evidence,explanation,created_at) VALUES(:id,:history,:indicator,:score,:detected,'[]','',:now)"),{"id":str(uuid.uuid4()),"history":history_id,"indicator":name,"score":float(score),"detected":float(score)>0,"now":now})
        return self.history_detail(user_id,history_id)

    def histories(self,user_id:str,query:str="",category:str|None=None,risk:str|None=None,favorite:bool|None=None)->list[dict]:
        self.purge_expired(); clauses=["user_id=:user","deleted_at IS NULL"]; params={"user":user_id,"query":f"%{query.casefold()}%"}
        if query: clauses.append("(lower(safe_title) LIKE :query OR lower(summary) LIKE :query)")
        if category: clauses.append("category=:category");params["category"]=category
        if risk: clauses.append("risk_level=:risk");params["risk"]=risk
        if favorite is not None: clauses.append("is_favorite=:favorite");params["favorite"]=favorite
        with self.engine.connect() as db: rows=db.execute(text(f"SELECT id,safe_title,anonymized_text,category,risk_level,risk_score,confidence_score,summary,is_favorite,created_at,updated_at FROM user_analysis_histories WHERE {' AND '.join(clauses)} ORDER BY created_at DESC"),params).mappings().all()
        return [{**dict(row),"is_favorite":bool(row["is_favorite"])} for row in rows]

    def history_detail(self,user_id:str,history_id:str)->dict|None:
        with self.engine.connect() as db:
            row=db.execute(text("SELECT * FROM user_analysis_histories WHERE id=:id AND user_id=:user AND deleted_at IS NULL"),{"id":history_id,"user":user_id}).mappings().first()
            if not row:return None
            indicators=db.execute(text("SELECT indicator,score,detected,anonymized_evidence,explanation FROM user_analysis_indicators WHERE analysis_history_id=:id"),{"id":history_id}).mappings().all()
        item=dict(row);item["is_favorite"]=bool(item["is_favorite"]);item["indicators"]=[{**dict(x),"detected":bool(x["detected"])} for x in indicators]
        for key in ("explanation","warning_signs","recommendations"):
            try:item[key]=json.loads(item[key] or "[]")
            except Exception:item[key]=[]
        return item

    def update_history(self,user_id:str,history_id:str,payload:dict)->dict|None:
        values={k:v for k,v in payload.items() if k in {"is_favorite","personal_note"}}; values.update(user=user_id,id=history_id,now=datetime.now(timezone.utc))
        with self.engine.begin() as db:
            result=db.execute(text("UPDATE user_analysis_histories SET "+",".join(f"{k}=:{k}" for k in values if k not in {'user','id','now'})+",updated_at=:now WHERE id=:id AND user_id=:user AND deleted_at IS NULL"),values) if len(values)>3 else None
        return self.history_detail(user_id,history_id) if result and result.rowcount else None

    def delete_history(self,user_id:str,history_id:str)->bool:
        with self.engine.begin() as db:r=db.execute(text("UPDATE user_analysis_histories SET deleted_at=:now WHERE id=:id AND user_id=:user AND deleted_at IS NULL"),{"now":datetime.now(timezone.utc),"id":history_id,"user":user_id})
        return bool(r.rowcount)

    def delete_all(self,user_id:str)->int:
        with self.engine.begin() as db:r=db.execute(text("UPDATE user_analysis_histories SET deleted_at=:now WHERE user_id=:user AND deleted_at IS NULL"),{"now":datetime.now(timezone.utc),"user":user_id})
        return r.rowcount

    def dashboard(self,user_id:str)->dict:
        rows=self.histories(user_id); reports=self.reports(user_id); guides=self.saved_guides(user_id)
        return {"total_analyses":len(rows),"risk_counts":{level:sum(1 for x in rows if x["risk_level"]==level) for level in ("LOW","MEDIUM","HIGH")},"total_reports":len(reports),"saved_guides":len(guides),"recent_histories":rows[:5],"recent_reports":reports[:3],"privacy":self.privacy(user_id)}

    def reports(self,user_id:str)->list[dict]:
        with self.engine.connect() as db:rows=db.execute(text("SELECT id,anonymized_text,category_suggested,status,created_at,updated_at,rejection_reason FROM reports WHERE user_id=:user AND user_hidden_at IS NULL AND deleted_at IS NULL ORDER BY created_at DESC"),{"user":user_id}).mappings().all()
        return [dict(x) for x in rows]

    def report_detail(self,user_id:str,report_id:str)->dict|None:
        with self.engine.connect() as db:row=db.execute(text("SELECT id,anonymized_text,category_suggested,status,created_at,updated_at,rejection_reason,admin_result FROM reports WHERE id=:id AND user_id=:user AND user_hidden_at IS NULL"),{"id":report_id,"user":user_id}).mappings().first()
        return dict(row) if row else None

    def saved_guides(self,user_id:str)->list[dict]:
        with self.engine.connect() as db:rows=db.execute(text("SELECT g.id AS saved_id,e.id,e.title,e.category,e.description,e.summary,e.thumbnail,e.updated_at FROM user_saved_guides g JOIN education_items e ON e.id=g.education_content_id WHERE g.user_id=:user AND e.is_published=TRUE AND e.deleted_at IS NULL ORDER BY g.created_at DESC"),{"user":user_id}).mappings().all()
        return [dict(x) for x in rows]

    def save_guide(self,user_id:str,guide_id:str)->None:
        with self.engine.begin() as db:db.execute(text("INSERT INTO user_saved_guides(id,user_id,education_content_id,created_at) SELECT :id,:user,:guide,:now WHERE EXISTS(SELECT 1 FROM education_items WHERE id=:guide AND is_published=TRUE) AND NOT EXISTS(SELECT 1 FROM user_saved_guides WHERE user_id=:user AND education_content_id=:guide)"),{"id":str(uuid.uuid4()),"user":user_id,"guide":guide_id,"now":datetime.now(timezone.utc)})

    def remove_guide(self,user_id:str,guide_id:str)->bool:
        with self.engine.begin() as db:r=db.execute(text("DELETE FROM user_saved_guides WHERE user_id=:user AND education_content_id=:guide"),{"user":user_id,"guide":guide_id})
        return bool(r.rowcount)

    def purge_expired(self)->int:
        with self.engine.begin() as db:r=db.execute(text("UPDATE user_analysis_histories SET deleted_at=:now WHERE deleted_at IS NULL AND retention_expires_at IS NOT NULL AND retention_expires_at<:now"),{"now":datetime.now(timezone.utc)})
        return r.rowcount

    def export(self,user_id:str)->dict:
        user=self.store.get_user(user_id) or {}; return {"profile":{k:user.get(k) for k in ("id","name","email","created_at","last_login_at")},"histories":[self.history_detail(user_id,x["id"]) for x in self.histories(user_id)],"reports":self.reports(user_id),"saved_guides":self.saved_guides(user_id),"privacy":self.privacy(user_id)}

    def request_reset(self,email:str)->str|None:
        user=self.store.get_user_by_email(email)
        if not user:return None
        token=secrets.token_urlsafe(32);import hashlib;digest=hashlib.sha256(token.encode()).hexdigest();now=datetime.now(timezone.utc)
        with self.engine.begin() as db:db.execute(text("INSERT INTO password_reset_tokens(token_hash,user_id,expires_at,created_at) VALUES(:token,:user,:expires,:now)"),{"token":digest,"user":user["id"],"expires":now+timedelta(minutes=30),"now":now})
        return token

    def reset_password(self,token:str,password:str,revoke:bool=True)->bool:
        import hashlib;digest=hashlib.sha256(token.encode()).hexdigest();now=datetime.now(timezone.utc)
        with self.engine.begin() as db:
            row=db.execute(text("SELECT user_id FROM password_reset_tokens WHERE token_hash=:token AND used_at IS NULL AND expires_at>:now"),{"token":digest,"now":now}).mappings().first()
            if not row:return False
            db.execute(text("UPDATE users SET password_hash=:password,updated_at=:now WHERE id=:user"),{"password":self.store._password_hash(password),"now":now,"user":row["user_id"]});db.execute(text("UPDATE password_reset_tokens SET used_at=:now WHERE token_hash=:token"),{"now":now,"token":digest})
            if revoke:db.execute(text("DELETE FROM user_sessions WHERE user_id=:user"),{"user":row["user_id"]})
        return True


def initialize_user_domain(store):
    return UserDomain(store)
