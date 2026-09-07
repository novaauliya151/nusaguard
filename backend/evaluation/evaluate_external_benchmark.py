"""Evaluasi otomatis IndoBERT dan IndoBERT+N-SEAE pada test set terpisah."""
from __future__ import annotations

import argparse, csv, hashlib, json, sys, time
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from app.services.nseae import analyze_nseae
from app.services.predictor import predict_category_with_fusion, predict_probabilities

DEFAULT_TEST = ROOT / "dataset" / "training" / "test.csv"
DEFAULT_OUTPUT = BACKEND / "evaluation" / "results"

def normalized_hash(value: str) -> str:
    return hashlib.sha256(" ".join(value.casefold().split()).encode()).hexdigest()

def read_rows(path: Path) -> list[dict[str, str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    if not rows: raise SystemExit("Dataset uji kosong.")
    columns = set(rows[0])
    if {"text", "expected"} <= columns:
        return [{"text": r["text"].strip(), "expected": r["expected"].strip(),
                 "source_id": r.get("source_id") or f"sample-{i+1:04d}"} for i, r in enumerate(rows)]
    if {"Pesan", "Kategori_NusaGuard"} <= columns:
        return [{"text": r["Pesan"].strip(), "expected": r["Kategori_NusaGuard"].strip(),
                 "source_id": r.get("Template_ID") or f"sample-{i+1:04d}"} for i, r in enumerate(rows)]
    raise SystemExit("CSV harus memiliki kolom text+expected atau Pesan+Kategori_NusaGuard.")

def metrics(expected: list[str], predicted: list[str], labels: list[str]) -> dict:
    return {
        "accuracy": accuracy_score(expected, predicted),
        "precision_macro": precision_score(expected, predicted, labels=labels, average="macro", zero_division=0),
        "recall_macro": recall_score(expected, predicted, labels=labels, average="macro", zero_division=0),
        "f1_macro": f1_score(expected, predicted, labels=labels, average="macro", zero_division=0),
        "classification_report": classification_report(expected, predicted, labels=labels, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(expected, predicted, labels=labels).tolist(),
    }

def write_predictions(path: Path, rows: list[dict]) -> None:
    fields = ["source_id", "expected", "indobert_prediction", "fusion_prediction",
              "indobert_correct", "fusion_correct", "fusion_applied", "model_confidence",
              "fusion_confidence", "indobert_time_ms", "fusion_time_ms"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def write_class_report(path: Path, labels: list[str], baseline: dict, fused: dict) -> None:
    fields = ["system", "category", "precision", "recall", "f1_score", "support"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for system, report in (("IndoBERT", baseline), ("IndoBERT + N-SEAE", fused)):
            for label in labels:
                value = report["classification_report"][label]
                writer.writerow({"system": system, "category": label,
                    "precision": round(value["precision"], 4), "recall": round(value["recall"], 4),
                    "f1_score": round(value["f1-score"], 4), "support": int(value["support"])})

def write_matrix(path: Path, matrix: list[list[int]], labels: list[str]) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from sklearn.metrics import ConfusionMatrixDisplay
    except ImportError as error:
        raise SystemExit("Pasang matplotlib: pip install matplotlib") from error
    short = [x.replace("Phishing/Link Berbahaya", "Phishing").replace("Penipuan ", "").replace("Social Engineering", "Social Eng.") for x in labels]
    figure, axis = plt.subplots(figsize=(9, 7))
    ConfusionMatrixDisplay(np.asarray(matrix), display_labels=short).plot(ax=axis, cmap="Greens", colorbar=False, values_format="d")
    axis.set(title="Confusion Matrix IndoBERT + N-SEAE", xlabel="Prediksi sistem", ylabel="Label sebenarnya")
    plt.xticks(rotation=35, ha="right"); figure.tight_layout(); figure.savefig(path, dpi=200); plt.close(figure)

def main() -> None:
    parser = argparse.ArgumentParser(description="Uji otomatis IndoBERT vs IndoBERT+N-SEAE.")
    parser.add_argument("csv_path", nargs="?", type=Path, default=DEFAULT_TEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--training-hashes", type=Path)
    parser.add_argument("--allow-small", action="store_true")
    parser.add_argument("--matrix-only", action="store_true", help="Buat ulang PNG dari evaluation.json tanpa menguji model.")
    args = parser.parse_args()
    if args.matrix_only:
        output = args.output_dir.resolve()
        saved = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
        write_matrix(output / "confusion_matrix.png", saved["indobert_plus_nseae"]["confusion_matrix"], saved["labels"])
        print(f"Confusion matrix berhasil dibuat: {output / 'confusion_matrix.png'}")
        return
    rows = read_rows(args.csv_path)
    if len(rows) < 60 and not args.allow_small: raise SystemExit("Data uji minimal 60 sampel.")
    hashes = [normalized_hash(r["text"]) for r in rows]
    if len(set(hashes)) != len(hashes): raise SystemExit("Data uji mengandung teks duplikat.")
    training = set(json.loads(args.training_hashes.read_text())) if args.training_hashes else set()
    if set(hashes) & training: raise SystemExit("Terdapat data uji yang juga ada di data latih.")

    expected, baseline, fused, details, base_times, fusion_times = [], [], [], [], [], []
    for index, row in enumerate(rows, 1):
        started = time.perf_counter(); probabilities, _ = predict_probabilities(row["text"]); base_times.append((time.perf_counter()-started)*1000)
        if not probabilities: raise SystemExit("IndoBERT tidak aktif. Periksa backend/model/indobert.")
        base_label, model_confidence = max(probabilities.items(), key=lambda item: item[1])
        started = time.perf_counter(); _, scores = analyze_nseae(row["text"])
        _, fusion_label, fusion_confidence, _, applied, _ = predict_category_with_fusion(row["text"], scores)
        fusion_times.append((time.perf_counter()-started)*1000)
        expected.append(row["expected"]); baseline.append(base_label.value); fused.append(fusion_label.value)
        details.append({"source_id": row["source_id"], "expected": row["expected"],
            "indobert_prediction": base_label.value, "fusion_prediction": fusion_label.value,
            "indobert_correct": base_label.value == row["expected"], "fusion_correct": fusion_label.value == row["expected"],
            "fusion_applied": applied, "model_confidence": round(model_confidence, 4),
            "fusion_confidence": round(fusion_confidence, 4), "indobert_time_ms": round(base_times[-1], 2),
            "fusion_time_ms": round(fusion_times[-1], 2)})
        if index % 25 == 0 or index == len(rows): print(f"Menguji {index}/{len(rows)} pesan...", flush=True)

    labels = sorted(set(expected) | set(baseline) | set(fused)); base_result = metrics(expected, baseline, labels); fusion_result = metrics(expected, fused, labels)
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    result = {"scope": "Test set pengembangan terpisah; bukan klaim performa dunia nyata.",
        "dataset": str(args.csv_path.resolve()), "samples": len(rows), "labels": labels,
        "class_distribution": dict(Counter(expected)), "baseline_indobert": base_result,
        "indobert_plus_nseae": fusion_result, "fusion_delta_f1_macro": fusion_result["f1_macro"]-base_result["f1_macro"],
        "average_time_ms": {"indobert": round(mean(base_times), 2), "indobert_plus_nseae": round(mean(fusion_times), 2)}}
    (output/"evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_predictions(output/"predictions.csv", details); write_class_report(output/"classification_report.csv", labels, base_result, fusion_result)
    write_matrix(output/"confusion_matrix.png", fusion_result["confusion_matrix"], labels)
    summary = {"samples": len(rows), "IndoBERT": {k: round(base_result[k]*100, 2) for k in ("accuracy", "precision_macro", "recall_macro", "f1_macro")},
        "IndoBERT + N-SEAE": {k: round(fusion_result[k]*100, 2) for k in ("accuracy", "precision_macro", "recall_macro", "f1_macro")}, "output": str(output)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
