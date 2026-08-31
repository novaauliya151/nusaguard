"""Unduh artefak model terpin bila deployment tidak membundel bobot model."""
import os
from pathlib import Path

def main():
    target=Path(os.getenv("NUSAGUARD_MODEL_PATH",Path(__file__).resolve().parents[1]/"model"/"indobert"));repo=os.getenv("NUSAGUARD_MODEL_REPO");revision=os.getenv("NUSAGUARD_MODEL_REVISION")
    if (target/"config.json").exists():print(f"Model tersedia: {target}");return
    if not repo:print("NUSAGUARD_MODEL_REPO tidak diatur; backend akan memakai rules-fallback.");return
    if not revision or revision=="main":raise SystemExit("Set NUSAGUARD_MODEL_REVISION ke commit SHA/tag immutable untuk deployment.")
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=repo,revision=revision,local_dir=target)
    print(f"Model {repo}@{revision} siap di {target}")
if __name__=="__main__":main()
