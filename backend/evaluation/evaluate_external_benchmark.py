"""Evaluasi held-out CSV; tidak pernah melatih model atau mengubah label."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from app.services.nseae import analyze_nseae
from app.services.predictor import predict_category_with_fusion, predict_probabilities


def normalized_hash(value: str) -> str:
    return hashlib.sha256(" ".join(value.casefold().split()).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluasi IndoBERT vs IndoBERT+N-SEAE pada data held-out nyata.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--training-hashes", type=Path, help="JSON array hash SHA-256 untuk pemeriksaan kebocoran data.")
    parser.add_argument("--output", type=Path, default=Path("evaluation/external_benchmark_results.json"))
    parser.add_argument("--allow-small", action="store_true")
    args = parser.parse_args()
    rows = list(csv.DictReader(args.csv_path.open(encoding="utf-8-sig")))
    required = {"text", "expected", "source_id"}
    if not rows or not required <= set(rows[0]):
        raise SystemExit(f"CSV wajib memiliki kolom: {', '.join(sorted(required))}")
    if len(rows) < 60 and not args.allow_small:
        raise SystemExit("Benchmark minimal 60 sampel. Gunakan --allow-small hanya untuk smoke test.")
    hashes = [normalized_hash(row["text"]) for row in rows]
    if len(set(hashes)) != len(hashes):
        raise SystemExit("Benchmark mengandung teks duplikat.")
    training = set(json.loads(args.training_hashes.read_text())) if args.training_hashes else set()
    leaked = sorted(set(hashes) & training)
    if leaked:
        raise SystemExit(f"Terdeteksi {len(leaked)} sampel yang juga ada pada data latih.")

    expected, baseline, fused, details = [], [], [], []
    for row in rows:
        probabilities, source = predict_probabilities(row["text"])
        if not probabilities:
            raise SystemExit("IndoBERT tidak aktif. Set NUSAGUARD_MODEL_PATH atau NUSAGUARD_MODEL_REPO.")
        base = max(probabilities.items(), key=lambda item: item[1])[0].value
        _, scores = analyze_nseae(row["text"])
        _, fusion, confidence, _, applied, model_confidence = predict_category_with_fusion(row["text"], scores)
        expected.append(row["expected"]); baseline.append(base); fused.append(fusion.value)
        details.append({"source_id": row["source_id"], "expected": row["expected"], "baseline": base, "fused": fusion.value, "fusion_applied": applied, "model_confidence": round(model_confidence, 4), "fused_confidence": round(confidence, 4), "model_source": source})
    labels = sorted(set(expected) | set(baseline) | set(fused))
    def metrics(predicted: list[str]) -> dict:
        return {"accuracy": accuracy_score(expected, predicted), "f1_macro": f1_score(expected, predicted, average="macro", zero_division=0), "classification_report": classification_report(expected, predicted, labels=labels, output_dict=True, zero_division=0), "confusion_matrix": confusion_matrix(expected, predicted, labels=labels).tolist()}
    result = {"claim_limit": "Held-out benchmark; validity depends on documented, independent sampling.", "samples": len(rows), "labels": labels, "class_distribution": Counter(expected), "baseline_indobert": metrics(baseline), "indobert_plus_nseae": metrics(fused), "fusion_delta_f1_macro": metrics(fused)["f1_macro"]-metrics(baseline)["f1_macro"], "details_without_raw_text": details}
    args.output.parent.mkdir(parents=True, exist_ok=True);args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key:value for key,value in result.items() if key!="details_without_raw_text"}, ensure_ascii=False, indent=2, default=dict))


if __name__ == "__main__": main()
