"use client";
/* eslint-disable react-hooks/set-state-in-effect */
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import UserSidebar, { MenuIcon, USER_MENUS, type UserView } from "./user.sidebar";
import UserAnalysis from "./user.analisis";
import UserDashboard from "./user.dashboard";
import History from "./user.riwayat";
import Reports from "./user.laporan";
import Guides from "./user.panduan.tersimpan";
import Privacy from "./user.privasi.keamanan";
import Profile from "./user.profil";
import { API } from "./user-api";
import styles from "./dashboard.module.css";
type User = {
  name: string;
  email: string;
  role: string;
  permissions: string[];
  last_login_at?: string;
  created_at?: string;
};
export default function UserShell() {
  const [user, setUser] = useState<User | null>(null),
    [menuOpen, setMenuOpen] = useState(false),
    [view, setView] = useState<UserView>("ringkasan");
  const router = useRouter(),
    search = useSearchParams();
  useEffect(() => {
    const requested = search.get("fitur") as UserView | null;
    if (
      requested &&
      (requested === "profil" || USER_MENUS.some((item) => item.key === requested))
    ) {
      setView(requested);
    }
    const token = localStorage.getItem("nusaguard_token");
    if (!token) {
      router.replace(`/masuk?next=${encodeURIComponent("/dashboard")}`);
      return;
    }
    fetch(`${API}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const account = await response.json();
        if (account.role !== "user") {
          router.replace("/admin");
          return;
        }
        setUser(account);
      })
      .catch(() => {
        localStorage.removeItem("nusaguard_token");
        router.replace("/masuk");
      });
  }, [router, search]);
  async function logout() {
    const token = localStorage.getItem("nusaguard_token");
    if (token)
      await fetch(`${API}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => null);
    localStorage.removeItem("nusaguard_token");
    router.push("/");
  }
  function navigate(next: UserView) {
    setView(next);
    setMenuOpen(false);
    history.replaceState(null, "", `/dashboard?fitur=${next}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  const closeMenu = useCallback(() => setMenuOpen(false), []);
  if (!user) return <main className={styles.loading}>Memuat pusat keamanan…</main>;
  const content = {
    ringkasan: (
      <UserDashboard
        openAnalyze={() => navigate("analisis")}
        openReport={() => navigate("laporan")}
      />
    ),
    analisis: <UserAnalysis />,
    riwayat: <History />,
    laporan: <Reports />,
    panduan: <Guides />,
    profil: <Profile user={user} onUpdate={(name) => setUser({ ...user, name })} />,
    privasi: <Privacy />,
  }[view];
  return (
    <div className={`${styles.shell} ${menuOpen ? styles.menuOpen : ""}`}>
      <UserSidebar
        open={menuOpen}
        activeView={view}
        user={user}
        onClose={closeMenu}
        onNavigate={navigate}
        onProfile={() => navigate("profil")}
        onLogout={() => void logout()}
      />
      <main>
        <header>
          <button
            className={styles.menuButton}
            onClick={() => setMenuOpen((current) => !current)}
            aria-label={menuOpen ? "Tutup sidebar" : "Buka sidebar"}
            aria-expanded={menuOpen}
            aria-controls="user-sidebar"
          >
            <MenuIcon />
          </button>
          <div>
            <p>DASHBOARD SAYA</p>
            <h1>
              {view === "ringkasan"
                ? `Halo, ${user.name.split(" ")[0]}`
                : (USER_MENUS.find((item) => item.key === view)?.label ?? "Profil")}
            </h1>
            {view !== "ringkasan" && (
              <small>
                Dashboard / {USER_MENUS.find((item) => item.key === view)?.label ?? "Profil"}
              </small>
            )}
          </div>
        </header>
        <section className={styles.content}>{content}</section>
        <footer>
          <span>NusaGuard · Akun opsional</span>
          <span>{user.email}</span>
        </footer>
      </main>
    </div>
  );
}
