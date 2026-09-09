"""Buat atau promosikan akun administrator NusaGuard secara lokal."""

from getpass import getpass
import re

from app.services.store import store


def main() -> None:
    name = input("Nama admin: ").strip()
    email = input("Email admin: ").strip().casefold()
    existing = store.get_user_by_email(email)
    if existing:
        store.update_user(existing["id"], "super_admin", True)
        print(f"Akun {email} dipromosikan menjadi admin. Kata sandi lama tetap berlaku.")
        return

    password = getpass("Kata sandi admin (minimal 14 karakter, lengkap): ")
    strong = len(password) >= 14 and all((re.search(r"[a-z]", password), re.search(r"[A-Z]", password), re.search(r"\d", password), re.search(r"[^A-Za-z0-9]", password)))
    if not strong:
        raise SystemExit("Kata sandi wajib memuat huruf kecil, huruf besar, angka, dan simbol.")
    user = store.create_user(name, email, password, "super_admin")
    if not user:
        raise SystemExit("Akun admin gagal dibuat.")
    print(f"Akun admin {email} berhasil dibuat.")


if __name__ == "__main__":
    main()
