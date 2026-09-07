"use client";
import Link from "next/link";
import { Bell } from "lucide-react";
import LogoNusaGuard from "../../components/logo_nusaguard";
import { useRouter, useSearchParams } from "next/navigation";
import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { adminFetch, adminLogout, AdminUser, API, Dashboard } from "./admin-api";
import { AdminProvider } from "./admin-context";
import AdminSidebar, { ADMIN_NAV, AdminMenuIcon } from "./admin.sidebar";
import styles from "./admin.module.css";
export default function AdminShell({ children }: { children: ReactNode }) {
  const params = useSearchParams(),
    router = useRouter(),
    feature = params.get("fitur") ?? "dashboard";
  const [ready, setReady] = useState(false),
    [menuOpen, setMenuOpen] = useState(false),
    [error, setError] = useState(""),
    [user, setUser] = useState<AdminUser>({
      id: "",
      name: "",
      email: "",
      role: "",
      permissions: [],
      is_active: false,
      status: "inactive",
      avatar: null,
      must_change_password: false,
      last_login_at: null,
      created_by: null,
      updated_at: null,
      created_at: "",
    }),
    [status, setStatus] = useState<Dashboard | null>(null);
  useEffect(() => {
    const timer = setTimeout(async () => {
      const token = localStorage.getItem("nusaguard_token");
      if (!token) {
        router.replace("/login");
        return;
      }
      try {
        const response = await fetch(`${API}/api/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          current = await response.json();
        if (
          !response.ok ||
          !current.permissions.some((permission: string) =>
            ADMIN_NAV.some((item) => item[2] === permission),
          )
        ) {
          localStorage.removeItem("nusaguard_token");
          setError("Akun ini tidak memiliki hak panel admin.");
          return;
        }
        setUser(current);
        setReady(true);
        void adminFetch<Dashboard>("/api/admin/dashboard")
          .then(setStatus)
          .catch(() => setStatus(null));
      } catch {
        setError("Backend belum dapat dijangkau.");
      }
    }, 0);
    return () => clearTimeout(timer);
  }, [router]);
  const visible = useMemo(
      () => ADMIN_NAV.filter(([, , permission]) => user?.permissions.includes(permission)),
      [user],
    ),
    current = ADMIN_NAV.find(([id]) => id === feature) ?? ADMIN_NAV[0];
  useEffect(() => {
    if (ready && !visible.some(([id]) => id === feature)) router.replace("/admin");
  }, [feature, ready, router, visible]);
  async function logout() {
    await adminLogout();
    router.replace("/login");
  }
  const closeMenu = useCallback(() => setMenuOpen(false), []);
  if (ready && !user) return null;
  if (!ready)
    return (
      <main className={styles.loginShell}>
        <section className={styles.loginCard}>
          <div className={styles.loginBrand}>
            <LogoNusaGuard />
            <div>
              <b>NusaGuard</b>
              <small>AREA TERLINDUNGI</small>
            </div>
          </div>
          <p className={styles.kicker}>OTORISASI BERBASIS ROLE</p>
          <h1>{error ? "Akses ditolak." : "Memverifikasi sesi…"}</h1>
          <p>{error || "Hak akses akun sedang diperiksa oleh server."}</p>
          {error && <Link href="/login">Kembali ke halaman login</Link>}
        </section>
        <div className={styles.loginVisual}>
          <span>PRIVACY-FIRST OPERATIONS</span>
          <div className={styles.rings}>
            <i />
            <i />
            <b>N</b>
          </div>
          <p>Role dan permission berasal dari database serta diverifikasi oleh backend.</p>
        </div>
      </main>
    );
  return (
    <AdminProvider value={user}>
      <div className={styles.shell}>
        <AdminSidebar
          open={menuOpen}
          feature={feature}
          user={user}
          onClose={closeMenu}
          onLogout={() => void logout()}
        />
        <main className={styles.main}>
          <header>
            <button
              className={styles.menu}
              onClick={() => setMenuOpen((v) => !v)}
              aria-label={menuOpen ? "Tutup sidebar" : "Buka sidebar"}
              aria-expanded={menuOpen}
            >
              <AdminMenuIcon />
            </button>
            <div className={styles.headerTitle}>
              <p>ADMIN / {current[1].toUpperCase()}</p>
              <h1>{current[1]}</h1>
            </div>
            <div className={styles.headerRight}>
              <span className={styles.live}>
                ● {status ? status.model_status.toUpperCase() : "STATUS AI TIDAK TERSEDIA"}
              </span>
              {user.permissions.includes("reports.view") && (
                <details className={styles.notificationMenu}>
                  <summary
                    className={styles.notification}
                    title={`${status?.reports_pending ?? 0} laporan menunggu`}
                    aria-label={`${status?.reports_pending ?? 0} laporan menunggu`}
                  >
                    <Bell aria-hidden="true" />
                    {(status?.reports_pending ?? 0) > 0 && <b>{status?.reports_pending}</b>}
                  </summary>
                  <div>
                    <header>
                      <strong>Pemberitahuan</strong>
                      <small>{status?.reports_pending ?? 0} laporan menunggu</small>
                    </header>
                    {(
                      status?.recent_reports
                        .filter((report) => report.status === "pending")
                        .slice(0, 4) ?? []
                    ).map((report) => (
                      <Link href="/admin?fitur=reports" key={report.id}>
                        <FileTextIcon />
                        <span>
                          <b>Laporan baru</b>
                          <small>{report.category_suggested}</small>
                        </span>
                      </Link>
                    ))}
                    {(status?.reports_pending ?? 0) === 0 && <p>Tidak ada laporan baru.</p>}
                    <Link className={styles.notificationAll} href="/admin?fitur=reports">
                      Buka laporan modus
                    </Link>
                  </div>
                </details>
              )}
            </div>
          </header>
          <section className={styles.content}>{children}</section>
          <footer>
            <span>NusaGuard Admin Console</span>
            <span>RBAC · audit aktif · analisis ephemeral</span>
          </footer>
        </main>
      </div>
    </AdminProvider>
  );
}

function FileTextIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6M8 13h8M8 17h5" />
    </svg>
  );
}
