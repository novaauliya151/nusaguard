"use client";
import { useEffect, useState } from "react";
import { userFetch } from "./user-api";
import styles from "./dashboard.module.css";
type Data = {
  total_analyses: number;
  total_reports: number;
};

type UserDashboardProps = {
  openAnalyze: () => void;
  openReport: () => void;
};

export default function UserDashboard({ openAnalyze, openReport }: UserDashboardProps) {
  const [data, setData] = useState<Data | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    userFetch<Data>("/api/user/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className={styles.userDashboard}>
      {error && <div className={styles.state}>{error}</div>}
      <div className={styles.pageHead}>
        <div>
          <p className={styles.kicker}>RINGKASAN AKTIVITAS</p>
          <h2>Aktivitas akunmu</h2>
          <p>Pantau jumlah analisis dan laporan yang sudah kamu buat.</p>
        </div>
      </div>
      <div className={styles.dashboardMetrics}>
        {[
          {
            label: "Total analisis",
            value: data?.total_analyses ?? 0,
            description: "Pesan yang telah kamu periksa",
          },
          {
            label: "Total laporan",
            value: data?.total_reports ?? 0,
            description: "Laporan penipuan yang kamu kirim",
          },
        ].map((metric) => (
          <article key={metric.label}>
            <small>{metric.label}</small>
            <strong>{metric.value}</strong>
            <p>{metric.description}</p>
          </article>
        ))}
      </div>
      <div className={styles.quickActions}>
        <div>
          <p className={styles.kicker}>AKSI CEPAT</p>
          <h3>Apa yang ingin kamu lakukan?</h3>
        </div>
        <button onClick={openAnalyze}>Analisis pesan</button>
        <button onClick={openReport}>Buat laporan</button>
      </div>
    </section>
  );
}
