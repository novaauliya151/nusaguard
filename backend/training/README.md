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

After training, compare the raw model with the N-SEAE fusion layer:

```bash
backend/.venv-ml/Scripts/python backend/evaluation/evaluate_nseae_ablation.py
```

The ablation result is written to `backend/evaluation/nseae_ablation_results.json`. It is explicitly scoped as a small curated challenge set and must not be generalized as production performance.

## Pengujian otomatis untuk presentasi

Jalankan dari root repository setelah model tersedia:

```powershell
backend/.venv/Scripts/python.exe backend/evaluation/evaluate_external_benchmark.py
```

Secara default script menguji seluruh `dataset/training/test.csv` dan membandingkan IndoBERT dengan IndoBERT + N-SEAE. Hasilnya disimpan di `backend/evaluation/results/` sebagai `evaluation.json`, `predictions.csv`, `classification_report.csv`, dan `confusion_matrix.png`.

Test set bawaan merupakan dataset pengembangan sintetis yang dipisahkan. Laporkan hasilnya sebagai evaluasi internal, bukan sebagai akurasi dunia nyata.

