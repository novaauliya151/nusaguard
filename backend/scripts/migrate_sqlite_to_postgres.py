"""Salin data NusaGuard dari SQLite lokal ke PostgreSQL/Supabase."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.dialects.postgresql import insert


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", default="nusaguard.db")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    target_url = os.getenv("DATABASE_URL", "")
    if not target_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
        raise SystemExit("DATABASE_URL harus menunjuk PostgreSQL/Supabase.")
    source_path = Path(args.sqlite).resolve()
    if not source_path.is_file():
        raise SystemExit(f"SQLite tidak ditemukan: {source_path}")

    target_url = target_url.replace("postgres://", "postgresql+psycopg://", 1)
    os.environ["DATABASE_URL"] = target_url
    from app.services.store import store

    source = create_engine(f"sqlite:///{source_path.as_posix()}")
    source_meta, target_meta = MetaData(), MetaData()
    source_meta.reflect(bind=source)
    target_meta.reflect(bind=store.engine)
    copied: dict[str, int] = {}

    with source.connect() as src, store.engine.begin() as dst:
        for target_table in target_meta.sorted_tables:
            source_table = source_meta.tables.get(target_table.name)
            if source_table is None:
                continue
            common = [column.name for column in target_table.columns if column.name in source_table.c]
            if not common:
                continue
            rows = src.execute(select(*(source_table.c[name] for name in common))).mappings()
            total = 0
            while batch := rows.fetchmany(args.batch_size):
                payload = [{name: row[name] for name in common} for row in batch]
                dst.execute(insert(target_table).values(payload).on_conflict_do_nothing())
                total += len(payload)
            copied[target_table.name] = total

    for table, count in copied.items():
        print(f"{table}: {count} baris diproses")
    print("Migrasi selesai. Primary key yang sudah ada tidak ditimpa.")


if __name__ == "__main__":
    main()
