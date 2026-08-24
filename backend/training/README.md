# IndoBERT training

From the repository root:

```bash
python -m venv backend/.venv-ml
backend/.venv-ml/Scripts/pip install -r backend/requirements-ml.txt
backend/.venv-ml/Scripts/python backend/training/train_indobert.py
```

The script fine-tunes `indobenchmark/indobert-base-p1`, evaluates the held-out test split, and writes real `accuracy` and macro-F1 values to `backend/model/indobert/evaluation.json`. Do not claim a model accuracy until this file has been produced by a completed run. The API uses an explicit `rules-fallback` until a valid model exists.
