"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { AnalyzeResponse } from "../types";
import styles from "./dashboard.module.css";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type User = { name:string; email:string; role:string; permissions:string[] };
type View = "home" | "analyze";

export default function Dashboard(){
  const [user,setUser]=useState<User|null>(null), [message,setMessage]=useState(""), [result,setResult]=useState<AnalyzeResponse|null>(null);
  const [error,setError]=useState(""), [loading,setLoading]=useState(false), [menuOpen,setMenuOpen]=useState(false);
  const [view,setView]=useState<View>("home");
  const router=useRouter();
  useEffect(()=>{const token=localStorage.getItem("nusaguard_token");if(!token){router.replace("/login");return}fetch(`${API}/api/auth/me`,{headers:{Authorization:`Bearer ${token}`}}).then(async r=>{if(!r.ok)throw new Error();setUser(await r.json())}).catch(()=>{localStorage.removeItem("nusaguard_token");router.replace("/login")})},[router]);
  async function analyze(){if(!message.trim())return;setLoading(true);setError("");try{const r=await fetch(`${API}/api/analyze`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:message,source:"user_dashboard"})});if(!r.ok)throw new Error();setResult(await r.json())}catch{setError("Analisis gagal. Periksa koneksi backend.")}finally{setLoading(false)}}
  function logout(){localStorage.removeItem("nusaguard_token");router.push("/login")}
  const closeMenu=()=>setMenuOpen(false);
  const navigate=(next:View)=>{setView(next);closeMenu();window.scrollTo({top:0,behavior:"smooth"})};
  if(!user)return <main className={styles.loading}>Memuat pusat keamanan…</main>;
  return <div className={`${styles.shell} ${menuOpen?styles.menuOpen:""}`}>
    <button className={styles.backdrop} onClick={closeMenu} aria-label="Tutup menu"/>
    <aside>
      <div className={styles.sideHead}><Link className={styles.logo} href="/"><span>NG</span><b>NusaGuard</b></Link><button className={styles.closeMenu} onClick={closeMenu} aria-label="Tutup sidebar">×</button></div>
      <nav><button className={view==="home"?styles.active:""} onClick={()=>navigate("home")}>⌂ Beranda</button><button className={view==="analyze"?styles.active:""} onClick={()=>navigate("analyze")}>⌁ Analisis pesan</button><Link href="/education" onClick={closeMenu}>▥ Edukasi modus</Link><Link href="/report" onClick={closeMenu}>◇ Lapor penipuan</Link><Link href="/dataset" onClick={closeMenu}>▦ Dataset publik</Link></nav>
      <div className={styles.account}><i>{user.name.slice(0,2).toUpperCase()}</i><div><b>{user.name}</b><small>{user.role}</small></div><button onClick={logout}>Keluar</button></div>
    </aside>
    <main>
      <header><button className={styles.menuButton} onClick={()=>setMenuOpen(true)} aria-label="Buka menu">☰</button><div><p>PUSAT KEAMANAN / {view.toUpperCase()}</p><h1>{view==="home"?`Halo, ${user.name.split(" ")[0]}.`:"Analisis pesan"}</h1></div><span>● TERLINDUNGI</span></header>
      <section className={styles.content}>
        {view==="home"&&<><div className={styles.hero}><div><p className={styles.kicker}>BERHENTI · PERIKSA · LINDUNGI</p><h2>Pesan mencurigakan?<br/><em>Periksa sebelum percaya.</em></h2><p>Analisis tetap ephemeral meskipun kamu login. NusaGuard tidak menyimpan isi pesan atau membuat histori percakapan.</p><button onClick={()=>navigate("analyze")}>Mulai analisis →</button></div><div className={styles.shield}>N</div></div><div className={styles.cards}><button onClick={()=>navigate("analyze")}><span>01</span><h3>Analisis instan</h3><p>Klasifikasi enam kategori dan skor risiko.</p></button><button onClick={()=>router.push("/report")}><span>02</span><h3>Lapor penipuan</h3><p>Kontribusikan contoh dengan consent dan privasi.</p></button><button onClick={()=>router.push("/education")}><span>03</span><h3>Kenali modus</h3><p>Pelajari edukasi terbaru dari admin.</p></button></div></>}
        {view==="analyze"&&<section className={styles.analyzer}><div><p className={styles.kicker}>ANALISIS PESAN</p><h2>Tempel pesan di sini</h2><textarea maxLength={5000} value={message} onChange={e=>setMessage(e.target.value)} placeholder="Contoh: Segera kirim OTP agar akun tidak diblokir…"/><div className={styles.meta}><span>{message.length}/5000</span><button disabled={loading||!message.trim()} onClick={()=>void analyze()}>{loading?"Menganalisis…":"Analisis sekarang →"}</button></div>{error&&<p className={styles.error}>{error}</p>}</div><div className={`${styles.result} ${result?styles[result.risk_level.toLowerCase()]:""}`}>{!result?<div className={styles.empty}><span>⌁</span><h3>Hasil muncul di sini</h3><p>Teks tidak disimpan sebagai histori akun.</p></div>:<><span>RISIKO {result.risk_level}</span><strong>{Math.round(result.risk_score*100)}<small>/100</small></strong><h3>{result.category}</h3><p>{result.explanation}</p><div className={styles.recommend}><b>Langkah aman</b><p>{result.recommendation}</p></div></>}</div></section>}
      </section>
      <footer><span>NusaGuard · User Dashboard</span><span>{user.email}</span></footer>
    </main>
  </div>
}

