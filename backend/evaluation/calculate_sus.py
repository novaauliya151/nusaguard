"""Hitung System Usability Scale dari CSV anonim: participant_id,q1..q10."""
import argparse,csv,json
from pathlib import Path

def score(row:dict[str,str])->float:
    values=[int(row[f"q{i}"]) for i in range(1,11)]
    if any(value not in range(1,6) for value in values):raise ValueError("Semua jawaban harus bernilai 1–5.")
    return sum((value-1 if index%2==0 else 5-value) for index,value in enumerate(values))*2.5

def main():
    parser=argparse.ArgumentParser();parser.add_argument("csv_path",type=Path);parser.add_argument("--output",type=Path,default=Path("evaluation/sus_results.json"));args=parser.parse_args()
    rows=list(csv.DictReader(args.csv_path.open(encoding="utf-8-sig")));scores=[score(row) for row in rows]
    if not scores:raise SystemExit("Belum ada respons SUS.")
    result={"participants":len(scores),"mean_sus":round(sum(scores)/len(scores),2),"minimum":min(scores),"maximum":max(scores),"individual_scores":[{"participant_id":row.get("participant_id",str(i+1)),"score":scores[i]} for i,row in enumerate(rows)]}
    args.output.write_text(json.dumps(result,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in result.items() if k!="individual_scores"},indent=2))
if __name__=="__main__":main()
