"""Membuat/memperbarui tabel akun opsional dan data pribadi user."""
from app.services.store import user_domain

if __name__ == "__main__":
    user_domain.initialize()
    removed = user_domain.purge_expired()
    print(f"Migrasi user selesai. Riwayat kedaluwarsa dibersihkan: {removed}")
