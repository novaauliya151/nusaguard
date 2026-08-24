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
            db.execute(text("CREATE TABLE IF NOT EXISTS reports (id VARCHAR(36) PRIMARY KEY, text TEXT NOT NULL, category_suggested VARCHAR(80) NOT NULL, created_at TIMESTAMP NOT NULL)"))
            db.execute(text("CREATE TABLE IF NOT EXISTS stats (category VARCHAR(80) PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0)"))
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

store = Store()
