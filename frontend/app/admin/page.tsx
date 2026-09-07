"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Dashboard from "./admin.dashboard";
import Users from "./admin.manajemen-pengguna";
import Reports from "./admin.laporan-modus";
import Dataset from "./admin.dataset";
import Nseae from "./admin.nseae";
import Education from "./admin.konten";
import Statistics from "./admin.statistik";
import Model from "./admin.monitoring";
import Activities from "./admin.log-aktivitas";
import Profile from "./admin.profil";
const pages: Record<string, React.ComponentType> = {
  dashboard: Dashboard,
  users: Users,
  reports: Reports,
  dataset: Dataset,
  nseae: Nseae,
  education: Education,
  statistics: Statistics,
  model: Model,
  activities: Activities,
  profile: Profile,
};
function Feature() {
  const params = useSearchParams(),
    Page = pages[params.get("fitur") ?? "dashboard"] ?? Dashboard;
  return <Page />;
}
export default function AdminPage() {
  return (
    <Suspense fallback={<div>Memuat halaman…</div>}>
      <Feature />
    </Suspense>
  );
}
