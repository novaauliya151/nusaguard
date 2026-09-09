"""Unggah artefak IndoBERT ke repositori Hugging Face privat."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi


REQUIRED = {"config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.getenv("HF_MODEL_REPO"))
    parser.add_argument("--model-dir", default="model/indobert")
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    if not args.repo:
        raise SystemExit("Set HF_MODEL_REPO atau gunakan --repo username/nusaguard-indobert.")
    model_dir = Path(args.model_dir).resolve()
    missing = sorted(name for name in REQUIRED if not (model_dir / name).is_file())
    if missing:
        raise SystemExit(f"Artefak model belum lengkap: {', '.join(missing)}")
    api = HfApi(token=os.getenv("HF_TOKEN"))
    api.create_repo(args.repo, repo_type="model", private=not args.public, exist_ok=True)
    api.upload_folder(
        repo_id=args.repo,
        repo_type="model",
        folder_path=model_dir,
        ignore_patterns=["training_args.bin", "*.tmp"],
        commit_message="Publish NusaGuard IndoBERT artifacts",
    )
    info = api.model_info(args.repo)
    print(f"Model tersedia di {args.repo}, revision {info.sha}")
    print("Gunakan SHA tersebut sebagai NUSAGUARD_MODEL_REVISION.")


if __name__ == "__main__":
    main()
