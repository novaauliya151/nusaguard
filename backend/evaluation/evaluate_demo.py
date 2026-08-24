import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.predictor import predict_category

root = Path(__file__).parent
cases = json.loads((root / "demo_cases.json").read_text(encoding="utf-8"))
rows=[]
for case in cases:
    _, predicted, confidence, source = predict_category(case["text"])
    rows.append({**case,"predicted":predicted.value,"confidence":confidence,"correct":predicted.value==case["expected"]})
report={"scope":"curated demo smoke test; not a held-out IndoBERT benchmark","model_source":rows[0]["predicted"] and source,"samples":len(rows),"accuracy":sum(r["correct"] for r in rows)/len(rows),"results":rows}
(root / "demo_results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
