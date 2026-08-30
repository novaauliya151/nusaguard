"""Jalankan migrasi idempoten schema admin NusaGuard."""
from app.services.store import admin_domain

if __name__ == "__main__":
    admin_domain.initialize()
    print("Migrasi schema admin NusaGuard selesai.")
