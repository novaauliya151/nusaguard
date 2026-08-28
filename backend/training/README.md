# IndoBERT training

From the repository root:

```bash
python -m venv backend/.venv-ml
backend/.venv-ml/Scripts/pip install -r backend/requirements-ml.txt
backend/.venv-ml/Scripts/python backend/training/train_indobert.py
```

Untuk mesin tanpa GPU, jalankan satu epoch awal agar model lokal aktif terlebih dahulu:

```bash
backend/.venv-ml/Scripts/python backend/training/train_indobert.py --epochs 1 --cpu
```

The script fine-tunes `indobenchmark/indobert-base-p1`, evaluates the held-out test split, and writes accuracy, macro-F1, per-class metrics, and a confusion matrix to `backend/model/indobert/evaluation.json`. The included split is synthetic development data, so its score must not be presented as real-world accuracy. The API uses an explicit `rules-fallback` until a valid model exists.

