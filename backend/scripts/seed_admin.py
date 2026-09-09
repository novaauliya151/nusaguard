"""Seed role, permission, referensi, dan Super Admin dari environment."""
import os
import re
from app.services.store import admin_domain, store

if __name__ == "__main__":
    admin_domain.initialize()
    email, password = os.getenv("INITIAL_ADMIN_EMAIL"), os.getenv("INITIAL_ADMIN_PASSWORD")
    if not email or not password:
        raise SystemExit("Set INITIAL_ADMIN_EMAIL dan INITIAL_ADMIN_PASSWORD terlebih dahulu.")
    if len(password) < 14 or not all((re.search(r"[a-z]", password), re.search(r"[A-Z]", password), re.search(r"\d", password), re.search(r"[^A-Za-z0-9]", password))):
        raise SystemExit("INITIAL_ADMIN_PASSWORD minimal 14 karakter dan wajib memuat huruf kecil, huruf besar, angka, serta simbol.")
    if store.get_user_by_email(email):
        print(f"Akun {email} sudah tersedia; seed referensi selesai.")
    else:
        user = admin_domain.create_internal_user({"name":os.getenv("INITIAL_ADMIN_NAME","Super Admin"),"email":email,"password":password,"role":"super_admin","status":"active","must_change_password":True}, "system")
        print(f"Super Admin {user['email']} berhasil dibuat dan wajib mengganti password.")
