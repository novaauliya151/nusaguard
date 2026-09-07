"""Isi statistik demo lima modus tanpa menghapus statistik yang sudah ada."""

from datetime import datetime, timezone

from sqlalchemy import text

from app.services.store import store


CATEGORY_MINIMUMS = {
    "Phishing/Link Berbahaya": 180,
    "Social Engineering": 140,
    "Penipuan Investasi": 110,
    "Penipuan Rekrutmen": 85,
    "Penipuan Romansa": 65,
}


def main() -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    month = today[:7]

    with store.lock, store.engine.begin() as db:
        current = {
            row["category"]: int(row["count"])
            for row in db.execute(
                text("SELECT category,count FROM stats WHERE category <> 'Aman'")
            ).mappings()
        }
        highest_existing = max(current.values(), default=0)
        targets = dict(CATEGORY_MINIMUMS)
        targets["Phishing/Link Berbahaya"] = max(
            targets["Phishing/Link Berbahaya"], highest_existing + 25
        )

        for category, target in targets.items():
            db.execute(
                text(
                    "INSERT INTO stats(category,count) VALUES (:category,:count) "
                    "ON CONFLICT(category) DO UPDATE SET count="
                    "CASE WHEN stats.count < :count THEN :count ELSE stats.count END"
                ),
                {"category": category, "count": target},
            )

        month_counts = {
            row["category"]: int(row["count"])
            for row in db.execute(
                text(
                    "SELECT category,SUM(count) AS count FROM stats_daily "
                    "WHERE day LIKE :month AND category <> 'Aman' AND source <> 'demo_seed' "
                    "GROUP BY category"
                ),
                {"month": f"{month}%"},
            ).mappings()
        }
        highest_month = max(month_counts.values(), default=0)
        daily_targets = {
            "Phishing/Link Berbahaya": max(80, highest_month + 20),
            "Social Engineering": 55,
            "Penipuan Investasi": 42,
            "Penipuan Rekrutmen": 31,
            "Penipuan Romansa": 24,
        }
        for category, count in daily_targets.items():
            db.execute(
                text(
                    "INSERT INTO stats_daily(day,category,source,count) "
                    "VALUES (:day,:category,'demo_seed',:count) "
                    "ON CONFLICT(day,category,source) DO UPDATE SET count=:count"
                ),
                {"day": today, "category": category, "count": count},
            )

    print("Statistik demo berhasil diisi. Phishing menjadi modus terbanyak.")


if __name__ == "__main__":
    main()
