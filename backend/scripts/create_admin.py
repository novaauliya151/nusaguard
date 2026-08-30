"""Buat atau promosikan akun administrator NusaGuard secara lokal."""

from getpass import getpass

from app.services.store import store


def main() -> None:
    name = input("Nama admin: ").strip()
    email = input("Email admin: ").strip().casefold()
    existing = store.get_user_by_email(email)
    if existing:
        store.update_user(existing["id"], "super_admin", True)
        print(f"Akun {email} dipromosikan menjadi admin. Kata sandi lama tetap berlaku.")
        return

    password = getpass("Kata sandi admin (minimal 8 karakter): ")
    if len(password) < 8:
        raise SystemExit("Kata sandi minimal 8 karakter.")
    user = store.create_user(name, email, password, "super_admin")
    if not user:
        raise SystemExit("Akun admin gagal dibuat.")
    print(f"Akun admin {email} berhasil dibuat.")


if __name__ == "__main__":
    main()
