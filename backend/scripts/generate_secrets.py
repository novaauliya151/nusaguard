"""Buat kredensial admin lokal yang kuat dan diabaikan Git."""

from __future__ import annotations

import argparse
import secrets
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="Email Super Admin")
    parser.add_argument("--output", default=".env", help="File keluaran")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"Menolak menimpa {output}.")
    password = secrets.token_urlsafe(24) + "aA1!"
    output.write_text(
        "INITIAL_ADMIN_NAME=Super Admin NusaGuard\n"
        f"INITIAL_ADMIN_EMAIL={args.email.strip()}\n"
        f"INITIAL_ADMIN_PASSWORD={password}\n",
        encoding="utf-8",
    )
    print(f"Secret admin disimpan ke {output}. File ini jangan di-commit.")


if __name__ == "__main__":
    main()
