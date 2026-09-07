"use client";
import { useEffect, useMemo, useState } from "react";
import { adminFetch, Dashboard } from "./admin-api";
import styles from "./admin.module.css";
type Stats = {
  average_response_ms: number;
  dataset_categories: Record<string, number>;
  indicators: Record<string, number>;
  daily: { day: string; count: number }[];
};
type Activity = {
  id: string;
  admin_email: string;
  action: string;
  object_type: string;
  created_at: string;
};
const colors: Record<string, string> = {
  "Phishing/Link Berbahaya": "#ff6b58",
  "Social Engineering": "#f4ad4d",
  "Penipuan Investasi": "#9e7df5",
  "Penipuan Rekrutmen": "#49a4e8",
  "Penipuan Romansa": "#eb70a0",
  Aman: "#65c88b",
};
export default function DashboardPage() {
  const now = new Date();
  const [data, setData] = useState<Dashboard | null>(null),
    [stats, setStats] = useState<Stats | null>(null),
    [period, setPeriod] = useState(
      `month:${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`,
    ),
    [activities, setActivities] = useState<Activity[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    void adminFetch<Dashboard>("/api/admin/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
    void adminFetch<Stats>("/api/admin/statistics")
      .then(setStats)
      .catch(() => setStats(null));
    void adminFetch<Activity[]>("/api/admin/activities")
      .then((value) => setActivities(value.slice(0, 5)))
      .catch(() => setActivities([]));
  }, []);
  useEffect(() => {
    const [kind, value] = period.split(":");
    const start = kind === "month" ? `${value}-01` : `${value}-01-01`;
    const endDate =
      kind === "month"
        ? new Date(Number(value.slice(0, 4)), Number(value.slice(5, 7)), 0)
        : new Date(Number(value), 11, 31);
    const end = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, "0")}-${String(endDate.getDate()).padStart(2, "0")}`;
    void adminFetch<Stats>(`/api/admin/statistics?start=${start}&end=${end}`)
      .then(setStats)
      .catch(() => setStats(null));
  }, [period]);
  const rows = useMemo(() => {
    const total = Math.max(data?.total_analyzed ?? 0, 1);
    return Object.entries(colors)
      .map(([name, color]) => ({
        name,
        color,
        count: data?.category_counts[name] ?? 0,
        percent: Math.round(((data?.category_counts[name] ?? 0) / total) * 100),
      }))
      .sort((a, b) => b.count - a.count);
  }, [data]);
  if (error)
    return (
      <div className={styles.alert}>
        {error}
        <button onClick={() => location.reload()}>Coba lagi</button>
      </div>
    );
  if (!data)
    return (
      <div className={styles.empty}>
        <h4>Memuat dashboard…</h4>
        <p>Mengambil data operasional dari database.</p>
      </div>
    );
  const chartRows = stats?.daily ?? [];
  const max = Math.max(...chartRows.map((x) => x.count), 1);
  const periodOptions = Array.from({ length: 12 }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth() - index, 1);
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    return {
      value: `month:${value}`,
      label: date.toLocaleDateString("id-ID", { month: "long", year: "numeric" }),
    };
  });
  const yearOptions = [...new Set(periodOptions.map((item) => item.value.slice(6, 10)))];
  return (
    <>
      <div className={styles.sectionHead}>
        <div>
          <span>GAMBARAN OPERASIONAL</span>
          <h2>Dashboard admin</h2>
        </div>
        <small>Diperbarui dari database</small>
      </div>
      {data.model_status.includes("fallback") && (
        <div className={styles.alert}>
          AI IndoBERT tidak aktif; sistem sedang memakai rules fallback.
        </div>
      )}
      <div className={`${styles.metrics} ${styles.dashboardTopMetrics}`}>
        <Metric
          label="Total analisis"
          value={data.total_analyzed}
          note="Tanpa menyimpan isi pesan"
        />
        <Metric label="Laporan disetujui" value={data.reports_reviewed} note="Sudah dimoderasi" />
      </div>
      <div className={styles.grid}>
        <section className={styles.panel}>
          <div className={styles.panelHead}>
            <div>
              <span>DISTRIBUSI DETEKSI</span>
              <h3>Kategori</h3>
            </div>
            <b>{data.total_analyzed} total</b>
          </div>
          <div className={styles.categoryList}>
            {rows.map((row) => (
              <div key={row.name}>
                <i style={{ background: row.color }} />
                <span>{row.name}</span>
                <div className={styles.bar}>
                  <b style={{ width: `${row.percent}%`, background: row.color }} />
                </div>
                <strong>{row.count}</strong>
                <small>{row.percent}%</small>
              </div>
            ))}
          </div>
        </section>
        <section className={`${styles.panel} ${styles.trend}`}>
          <div className={styles.panelHead}>
            <div>
              <span>TREN ANALISIS</span>
              <h3>Aktivitas analisis</h3>
            </div>
            <select
              className={styles.chartPeriod}
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              aria-label="Pilih periode grafik"
            >
              <optgroup label="Bulanan">
                {periodOptions.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Tahunan">
                {yearOptions.map((year) => (
                  <option key={year} value={`year:${year}`}>
                    Tahun {year}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>
          {chartRows.length ? (
            <div className={styles.chart}>
              {chartRows.map((x) => (
                <div key={x.day}>
                  <span>{x.count}</span>
                  <i style={{ height: `${Math.max(8, (x.count / max) * 100)}%` }} />
                  <small>{x.day.slice(5)}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.empty}>Belum ada tren.</div>
          )}
        </section>
        <List
          title="Laporan terbaru"
          rows={data.recent_reports.slice(0, 5).map((item) => ({
            id: item.id,
            title: item.category_suggested,
            detail: new Date(item.created_at).toLocaleString("id-ID"),
            value: item.status,
          }))}
        />
        {activities.length > 0 && (
          <List
            title="Aktivitas admin terbaru"
            rows={activities.map((item) => ({
              id: item.id,
              title: item.action,
              detail: `${item.admin_email} · ${item.object_type}`,
              value: new Date(item.created_at).toLocaleDateString("id-ID"),
            }))}
          />
        )}{" "}
        {stats && (
          <List
            title="Indikator N-SEAE"
            rows={Object.entries(stats.indicators)
              .sort((a, b) => b[1] - a[1])
              .map(([name, count]) => ({
                id: name,
                title: name.replaceAll("_", " "),
                detail: "Deteksi agregat",
                value: String(count),
              }))}
          />
        )}
      </div>
    </>
  );
}
function Metric({
  label,
  value,
  note,
  attention = false,
}: {
  label: string;
  value: string | number;
  note: string;
  attention?: boolean;
}) {
  return (
    <article className={attention ? styles.attention : ""}>
      <p>{label}</p>
      <strong className={typeof value === "string" ? styles.modelName : ""}>{value}</strong>
      <small>{note}</small>
    </article>
  );
}
function List({
  title,
  rows,
}: {
  title: string;
  rows: { id: string; title: string; detail: string; value: string }[];
}) {
  return (
    <section className={styles.panel}>
      <div className={styles.panelHead}>
        <h3>{title}</h3>
      </div>
      {rows.map((item) => (
        <div className={styles.systemRow} key={item.id}>
          <i>●</i>
          <div>
            <b>{item.title}</b>
            <small>{item.detail}</small>
          </div>
          <span>{item.value}</span>
        </div>
      ))}
    </section>
  );
}
