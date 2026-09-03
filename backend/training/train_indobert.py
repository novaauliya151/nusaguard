import argparse, csv, json, os
from pathlib import Path
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding

LABELS=["Aman","Phishing/Link Berbahaya","Social Engineering","Penipuan Investasi","Penipuan Rekrutmen","Penipuan Romansa"]
LABEL2ID={label:index for index,label in enumerate(LABELS)}

class CsvDataset(Dataset):
    def __init__(self,path,tokenizer,max_length):
        with path.open(encoding="utf-8-sig",newline="") as handle: rows=list(csv.DictReader(handle))
        self.encodings=tokenizer([row["Pesan"] for row in rows],truncation=True,max_length=max_length)
        self.labels=[LABEL2ID[row["Kategori_NusaGuard"]] for row in rows]
    def __len__(self): return len(self.labels)
    def __getitem__(self,index): return {**{key:value[index] for key,value in self.encodings.items()},"labels":self.labels[index]}

def evaluate(model,loader,device):
    model.eval(); predicted=[]; expected=[]; total=0.0
    with torch.inference_mode():
        for batch in loader:
            batch={key:value.to(device) for key,value in batch.items()}; output=model(**batch); total+=output.loss.item()
            predicted.extend(output.logits.argmax(1).cpu().tolist()); expected.extend(batch["labels"].cpu().tolist())
    return expected,predicted,total/max(len(loader),1)

def metrics(truth,pred):
    matrix=[[0 for _ in LABELS] for _ in LABELS]
    for expected,actual in zip(truth,pred): matrix[expected][actual]+=1
    report={}; f1_values=[]
    for index,label in enumerate(LABELS):
        tp=matrix[index][index]; fp=sum(row[index] for row in matrix)-tp; fn=sum(matrix[index])-tp
        precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0; f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        report[label]={"precision":precision,"recall":recall,"f1-score":f1,"support":sum(matrix[index])}; f1_values.append(f1)
    return sum(a==b for a,b in zip(truth,pred))/max(len(truth),1),sum(f1_values)/len(f1_values),report,matrix

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--model",default="indobenchmark/indobert-base-p1"); parser.add_argument("--data",default="dataset/training"); parser.add_argument("--output",default="model/indobert"); parser.add_argument("--epochs",type=int,default=3); parser.add_argument("--max-length",type=int,default=128); parser.add_argument("--batch-size",type=int,default=8); parser.add_argument("--cpu",action="store_true"); parser.add_argument("--cache-dir",default="backend/.cache/huggingface"); args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]; data=(root/args.data).resolve(); output=(root/"backend"/args.output).resolve(); cache=(root/args.cache_dir).resolve(); cache.mkdir(parents=True,exist_ok=True); os.environ.setdefault("HF_HOME",str(cache)); torch.manual_seed(42)
    device=torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda"); tokenizer=AutoTokenizer.from_pretrained(args.model,cache_dir=str(cache/"hub")); collator=DataCollatorWithPadding(tokenizer)
    sets={name:CsvDataset(data/f"{name}.csv",tokenizer,args.max_length) for name in ("train","val","test")}; loaders={name:DataLoader(value,batch_size=args.batch_size if name=="train" else max(args.batch_size,16),shuffle=name=="train",collate_fn=collator) for name,value in sets.items()}
    model=AutoModelForSequenceClassification.from_pretrained(args.model,num_labels=len(LABELS),id2label=dict(enumerate(LABELS)),label2id=LABEL2ID,cache_dir=str(cache/"hub")).to(device); optimizer=torch.optim.AdamW(model.parameters(),lr=2e-5); output.mkdir(parents=True,exist_ok=True); best=-1.0
    for epoch in range(args.epochs):
        model.train()
        for step,batch in enumerate(loaders["train"],1):
            batch={key:value.to(device) for key,value in batch.items()}; optimizer.zero_grad(set_to_none=True); loss=model(**batch).loss; loss.backward(); optimizer.step()
            if step%50==0: print(f"epoch={epoch+1} step={step}/{len(loaders['train'])} loss={loss.item():.4f}",flush=True)
        truth,pred,_=evaluate(model,loaders["val"],device); _,score,_,_=metrics(truth,pred); print(f"epoch={epoch+1} val_f1={score:.4f}",flush=True)
        if score>best: best=score; model.save_pretrained(output); tokenizer.save_pretrained(output)
    model=AutoModelForSequenceClassification.from_pretrained(output).to(device); truth,pred,loss=evaluate(model,loaders["test"],device)
    accuracy,macro_f1,report,matrix=metrics(truth,pred); results={"eval_loss":loss,"eval_accuracy":accuracy,"eval_f1_macro":macro_f1,"per_class":report,"confusion_matrix":matrix,"labels":LABELS,"dataset_split":{key:len(value) for key,value in sets.items()},"base_model":args.model,"epochs":args.epochs,"max_length":args.max_length,"warning":"Synthetic development benchmark; not a real-world performance claim."}
    (output/"evaluation.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps({key:results[key] for key in ("eval_accuracy","eval_f1_macro","dataset_split")},indent=2))

if __name__=="__main__": main()

