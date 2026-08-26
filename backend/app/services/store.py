import os
import threading
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

class Store:
    def __init__(self) -> None:
        url = os.getenv("DATABASE_URL", "sqlite:///nusaguard.db").replace("postgres://", "postgresql+psycopg://", 1)
        self.engine, self.lock = create_engine(url, pool_pre_ping=True), threading.Lock()
        with self.engine.begin() as db:
            db.execute(text("CREATE TABLE IF NOT EXISTS reports (id VARCHAR(36) PRIMARY KEY, text TEXT NOT NULL, category_suggested VARCHAR(80) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'pending', created_at TIMESTAMP NOT NULL)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS stats (category VARCHAR(80) PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0)"))
            columns = {row[1] for row in db.execute(text("PRAGMA table_info(reports)"))} if url.startswith("sqlite") else set()
            if columns and "status" not in columns:
                db.execute(text("ALTER TABLE reports ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'"))
    def increment(self, category: str) -> None:
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO stats(category,count) VALUES (:category,1) ON CONFLICT(category) DO UPDATE SET count=stats.count+1"), {"category":category})
    def stats(self) -> tuple[int, dict[str, int]]:
        with self.engine.connect() as db:
            counts={row.category:row.count for row in db.execute(text("SELECT category,count FROM stats"))}
        return sum(counts.values()), counts
    def report(self, content: str, category: str) -> tuple[str, datetime]:
        report_id, created = str(uuid.uuid4()), datetime.now(timezone.utc)
        with self.lock, self.engine.begin() as db:
            db.execute(text("INSERT INTO reports(id,text,category_suggested,created_at) VALUES (:id,:content,:category,:created)"), {"id":report_id,"content":content,"category":category,"created":created})
        return report_id, created

    def admin_dashboard(self, limit: int = 8) -> tuple[int, dict[str, int], int, int, list[dict]]:
        total, counts = self.stats()
        with self.engine.connect() as db:
            reports_total = db.execute(text("SELECT COUNT(*) FROM reports")).scalar_one()
            reports_pending = db.execute(text("SELECT COUNT(*) FROM reports WHERE status='pending'")).scalar_one()
            rows = db.execute(text("SELECT id,text,category_suggested,status,created_at FROM reports ORDER BY created_at DESC LIMIT :limit"), {"limit": limit}).mappings().all()
        return total, counts, reports_total, reports_pending, [dict(row) for row in rows]

    def update_report_status(self, report_id: str, status: str) -> bool:
        with self.lock, self.engine.begin() as db:
            result = db.execute(text("UPDATE reports SET status=:status WHERE id=:id"), {"status": status, "id": report_id})
        return result.rowcount > 0

store = Store()

