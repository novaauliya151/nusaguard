"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { AnalyzeResponse } from "../types";
import styles from "./dashboard.module.css";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type User = { name:string; email:string; role:string; permissions:string[] };

export default function Dashboard(){
  const [user,setUser]=useState<User|null>(null), [message,setMessage]=useState(""), [result,setResult]=useState<AnalyzeResponse|null>(null);
  const [error,setError]=useState(""), [loading,setLoading]=useState(false), [menuOpen,setMenuOpen]=useState(false);
  const router=useRouter();
  useEffect(()=>{const token=localStorage.getItem("nusaguard_token");if(!token){router.replace("/login");return}fetch(`${API}/api/auth/me`,{headers:{Authorization:`Bearer ${token}`}}).then(async r=>{if(!r.ok)throw new Error();setUser(await r.json())}).catch(()=>{localStorage.removeItem("nusaguard_token");router.replace("/login")})},[router]);
  async function analyze(){if(!message.trim())return;setLoading(true);setError("");try{const r=await fetch(`${API}/api/analyze`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:message,source:"user_dashboard"})});if(!r.ok)throw new Error();setResult(await r.json())}catch{setError("Analisis gagal. Periksa koneksi backend.")}finally{setLoading(false)}}
  function logout(){localStorage.removeItem("nusaguard_token");router.push("/login")}
  const closeMenu=()=>setMenuOpen(false);
  if(!user)return <main className={styles.loading}>Memuat pusat keamanan…</main>;
  return <div className={`${styles.shell} ${menuOpen?styles.menuOpen:""}`}>
    <button className={styles.backdrop} onClick={closeMenu} aria-label="Tutup menu"/>
    <aside>
      <div className={styles.sideHead}><Link className={styles.logo} href="/"><span>NG</span><b>NusaGuard</b></Link><button className={styles.closeMenu} onClick={closeMenu} aria-label="Tutup sidebar">×</button></div>
      <nav><a className={styles.active} href="#home" onClick={closeMenu}>⌂ Beranda</a><a href="#analyze" onClick={closeMenu}>⌁ Analisis pesan</a><a href="#access" onClick={closeMenu}>◇ Hak akses</a><Link href="/#edukasi" onClick={closeMenu}>▥ Edukasi modus</Link></nav>
      <div className={styles.account}><i>{user.name.slice(0,2).toUpperCase()}</i><div><b>{user.name}</b><small>{user.role}</small></div><button onClick={logout}>Keluar</button></div>
    </aside>
    <main>
      <header><button className={styles.menuButton} onClick={()=>setMenuOpen(true)} aria-label="Buka menu">☰</button><div><p>PUSAT KEAMANAN PENGGUNA</p><h1>Halo, {user.name.split(" ")[0]}.</h1></div><span>● TERLINDUNGI</span></header>
      <section id="home" className={styles.content}>
        <div className={styles.hero}><div><p className={styles.kicker}>BERHENTI · PERIKSA · LINDUNGI</p><h2>Pesan mencurigakan?<br/><em>Periksa sebelum percaya.</em></h2><p>Analisis tetap ephemeral meskipun kamu login. NusaGuard tidak menyimpan isi pesan atau membuat histori percakapan.</p><a href="#analyze">Mulai analisis →</a></div><div className={styles.shield}>N</div></div>
        <div className={styles.cards}><article><span>01</span><h3>Analisis instan</h3><p>Klasifikasi enam kategori dan skor risiko.</p></article><article><span>02</span><h3>Penjelasan transparan</h3><p>Enam indikator N-SEAE yang mudah dipahami.</p></article><article><span>03</span><h3>Rekomendasi aman</h3><p>Langkah praktis sebelum klik atau transfer.</p></article></div>
        <section id="analyze" className={styles.analyzer}><div><p className={styles.kicker}>ANALISIS PESAN</p><h2>Tempel pesan di sini</h2><textarea maxLength={5000} value={message} onChange={e=>setMessage(e.target.value)} placeholder="Contoh: Segera kirim OTP agar akun tidak diblokir…"/><div className={styles.meta}><span>{message.length}/5000</span><button disabled={loading||!message.trim()} onClick={()=>void analyze()}>{loading?"Menganalisis…":"Analisis sekarang →"}</button></div>{error&&<p className={styles.error}>{error}</p>}</div><div className={`${styles.result} ${result?styles[result.risk_level.toLowerCase()]:""}`}>{!result?<div className={styles.empty}><span>⌁</span><h3>Hasil muncul di sini</h3><p>Teks tidak disimpan sebagai histori akun.</p></div>:<><span>RISIKO {result.risk_level}</span><strong>{Math.round(result.risk_score*100)}<small>/100</small></strong><h3>{result.category}</h3><p>{result.explanation}</p><div className={styles.recommend}><b>Langkah aman</b><p>{result.recommendation}</p></div></>}</div></section>
        <section id="access" className={styles.access}><div><p className={styles.kicker}>ROLE & PERMISSION</p><h2>Akses akunmu</h2><p>Role menentukan fitur tambahan tanpa mengubah perlindungan dasar.</p></div><div><span className={styles.role}>{user.role}</span>{user.permissions.map(x=><p key={x}>✓ {x.replaceAll("_"," ")}</p>)}</div></section>
      </section>
      <footer><span>NusaGuard · User Dashboard</span><span>{user.email}</span></footer>
    </main>
  </div>
}

