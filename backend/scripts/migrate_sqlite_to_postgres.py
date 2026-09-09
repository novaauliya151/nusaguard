"""Copy SQLite rows to PostgreSQL, preserving references across unique-key conflicts."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from sqlalchemy import MetaData, UniqueConstraint, and_, create_engine, select
from sqlalchemy.dialects.postgresql import insert


def copy_data(source, target, batch_size=500):
    source_meta, target_meta = MetaData(), MetaData()
    source_meta.reflect(bind=source)
    target_meta.reflect(bind=target)
    mappings = {}
    counts = {}
    with source.connect() as src, target.begin() as dst:
        for table in target_meta.sorted_tables:
            old = source_meta.tables.get(table.name)
            if old is None:
                continue
            common = [c.name for c in table.columns if c.name in old.c]
            pk = list(table.primary_key.columns)
            unique_keys = [list(c.columns) for c in table.constraints if isinstance(c, UniqueConstraint)]
            unique_keys += [list(i.columns) for i in table.indexes if i.unique]
            keys = [pk] + unique_keys
            total = added = 0
            for row in src.execute(select(*(old.c[n] for n in common))).yield_per(batch_size).mappings():
                payload = dict(row)
                for fk in table.foreign_keys:
                    name = fk.parent.name
                    if name in payload:
                        payload[name] = mappings.get((fk.column.table.name, fk.column.name, payload[name]), payload[name])
                # Resolve a natural-key collision before inserting child references.
                matches = []
                for key in keys:
                    if key and all(c.name in payload and payload[c.name] is not None for c in key):
                        found = dst.execute(select(table).where(and_(*(c == payload[c.name] for c in key)))).mappings().first()
                        if found is not None:
                            matches.append(found)
                if matches:
                    existing = matches[0]
                    if any(tuple(m[c.name] for c in pk) != tuple(existing[c.name] for c in pk) for m in matches):
                        raise RuntimeError(f'Conflicting identities in table {table.name}; transaction rolled back')
                else:
                    existing = dst.execute(insert(table).values(payload).returning(*table.columns)).mappings().one()
                    added += 1
                for c in pk:
                    if c.name in row:
                        mappings[(table.name, c.name, row[c.name])] = existing[c.name]
                total += 1
            counts[table.name] = (total, added)
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite', default='nusaguard.db')
    parser.add_argument('--batch-size', type=int, default=500)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error('--batch-size must be positive')
    target_url = os.getenv('DATABASE_URL', '')
    if not target_url.startswith(('postgresql://', 'postgresql+psycopg://', 'postgres://')):
        raise SystemExit('DATABASE_URL harus menunjuk PostgreSQL/Supabase.')
    source_path = Path(args.sqlite).resolve()
    if not source_path.is_file():
        raise SystemExit('SQLite tidak ditemukan.')
    target_url = target_url.replace('postgres://', 'postgresql+psycopg://', 1).replace('postgresql://', 'postgresql+psycopg://', 1)
    os.environ['DATABASE_URL'] = target_url
    from app.services.store import store
    source = create_engine(f'sqlite:///{source_path.as_posix()}')
    for table, (total, added) in copy_data(source, store.engine, args.batch_size).items():
        print(f'{table}: {total} baris diverifikasi, {added} ditambahkan, {total-added} sudah ada')
    print('Migrasi selesai. Relasi ID dipetakan; data yang sudah ada tidak ditimpa.')

if __name__ == '__main__':
    main()
