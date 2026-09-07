"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import styles from "./public_chrome.module.css";

export default function FooterBeranda() {
  const [subscribed, setSubscribed] = useState(false);

  function subscribe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubscribed(true);
    event.currentTarget.reset();
  }

  return (
    <footer id="contact" className={styles.footer}>
      <div className={styles.footerGrid}>
        <section>
          <Link className={styles.footerBrand} href="/">
            <Image src="/images/logo_nusaguard.png" width={530} height={558} alt="Logo NusaGuard" />
            <b>NusaGuard</b>
          </Link>
          <p>
            NusaGuard membantu mengenali risiko social engineering dalam pesan berbahasa Indonesia.
            Hasil analisis disertai indikator dan langkah aman yang mudah dipahami.
          </p>
        </section>
        <section>
          <h2>Navigasi cepat</h2>
          <Link href="/">Home</Link>
          <Link href="/#analisis">Services</Link>
          <Link href="/education">Blog</Link>
          <Link href="/#contact">Contact</Link>
        </section>
        <section>
          <h2>Kontak</h2>
          <a href="mailto:nusaguard@gmail.com">nusaguard@gmail.com</a>
          {/*<span>Telepon: belum tersedia</span>*/}
          <span>Indonesia</span>
        </section>
        <section>
          <h2>Newsletter</h2>
          <p>Dapatkan pembaruan edukasi modus penipuan.</p>
          <form onSubmit={subscribe}>
            <label className={styles.srOnly} htmlFor="newsletter-email">
              Email newsletter
            </label>
            <input id="newsletter-email" type="email" required placeholder="nama@email.com" />
            <button type="submit">Subscribe</button>
          </form>
          {subscribed && (
            <small role="status">
              Terima kasih. Email belum disimpan karena layanan newsletter belum diaktifkan.
            </small>
          )}
        </section>
      </div>
      <div className={styles.footerBottom}>
        <span>© 2026 NusaGuard. All rights reserved.</span>
        <Link href="/privacy-policy">Privacy Policy</Link>
      </div>
    </footer>
  );
}
