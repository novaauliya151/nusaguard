import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, f1_score

from app.models.schemas import KategoriNusaGuard
from app.services.nseae import analyze_nseae
from app.services.predictor import predict_category_with_fusion, predict_probabilities


def binary(label: str) -> str:
    return "aman" if label == KategoriNusaGuard.AMAN.value else "penipuan"


def main() -> None:
    directory = Path(__file__).resolve().parent
    cases = json.loads((directory / "nseae_challenge_cases.json").read_text(encoding="utf-8"))
    expected, baseline, fused, details = [], [], [], []
    for case in cases:
        probabilities, source = predict_probabilities(case["text"])
        if not probabilities:
            raise RuntimeError("Artefak IndoBERT belum tersedia; evaluasi ablation memerlukan model aktif.")
        baseline_label = max(probabilities.items(), key=lambda item: item[1])[0]
        _, scores = analyze_nseae(case["text"])
        _, fused_label, confidence, _, applied, model_confidence = predict_category_with_fusion(case["text"], scores)
        expected.append(case["expected"])
        baseline.append(baseline_label.value)
        fused.append(fused_label.value)
        details.append({**case, "baseline": baseline_label.value, "fused": fused_label.value, "fusion_applied": applied, "model_confidence": round(model_confidence, 4), "fused_confidence": confidence})

    expected_binary = [binary(label) for label in expected]
    baseline_binary = [binary(label) for label in baseline]
    fused_binary = [binary(label) for label in fused]
    report = {
        "scope": "Curated 24-message challenge set; not a held-out real-world benchmark.",
        "samples": len(cases),
        "baseline_indobert": {
            "accuracy_multiclass": accuracy_score(expected, baseline),
            "f1_macro_multiclass": f1_score(expected, baseline, average="macro", zero_division=0),
            "f1_macro_binary": f1_score(expected_binary, baseline_binary, average="macro", zero_division=0),
            "binary_report": classification_report(expected_binary, baseline_binary, output_dict=True, zero_division=0),
        },
        "indobert_plus_nseae": {
            "accuracy_multiclass": accuracy_score(expected, fused),
            "f1_macro_multiclass": f1_score(expected, fused, average="macro", zero_division=0),
            "f1_macro_binary": f1_score(expected_binary, fused_binary, average="macro", zero_division=0),
            "binary_report": classification_report(expected_binary, fused_binary, output_dict=True, zero_division=0),
        },
        "fusion_applied_count": sum(row["fusion_applied"] for row in details),
        "details": details,
    }
    (directory / "nseae_ablation_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

