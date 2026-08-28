import argparse
import json
import os
from pathlib import Path

import numpy as np
from datasets import load_dataset
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, Trainer, TrainingArguments

LABELS = ["Aman", "Phishing/Link Berbahaya", "Social Engineering", "Penipuan Investasi", "Penipuan Rekrutmen", "Penipuan Romansa"]
LABEL2ID = {label: index for index, label in enumerate(LABELS)}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="indobenchmark/indobert-base-p1")
    parser.add_argument("--data", default="dataset/training")
    parser.add_argument("--output", default="model/indobert")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--cache-dir", default="backend/.cache/huggingface")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    data_dir, output = (root / args.data).resolve(), (root / "backend" / args.output).resolve()
    cache_dir = (root / args.cache_dir).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_dir))
    dataset = load_dataset("csv", data_files={split: str(data_dir / f"{split}.csv") for split in ("train", "val", "test")}, cache_dir=str(cache_dir / "datasets"))
    tokenizer = AutoTokenizer.from_pretrained(args.model, cache_dir=str(cache_dir / "hub"))
    def tokenize(batch):
        encoded = tokenizer(batch["Pesan"], truncation=True, max_length=args.max_length)
        encoded["labels"] = [LABEL2ID[label] for label in batch["Kategori_NusaGuard"]]
        return encoded
    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset["train"].column_names)
    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL2ID, cache_dir=str(cache_dir / "hub"))
    def metrics(prediction):
        predicted = np.argmax(prediction.predictions, axis=1)
        return {"accuracy": accuracy_score(prediction.label_ids, predicted), "f1_macro": f1_score(prediction.label_ids, predicted, average="macro")}
    trainer = Trainer(model=model, args=TrainingArguments(output_dir=str(output), num_train_epochs=args.epochs, learning_rate=2e-5, per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=max(args.batch_size, 16), eval_strategy="epoch", save_strategy="epoch", save_total_limit=1, load_best_model_at_end=True, metric_for_best_model="f1_macro", report_to="none", seed=42, use_cpu=args.cpu), train_dataset=tokenized["train"], eval_dataset=tokenized["val"], processing_class=tokenizer, data_collator=DataCollatorWithPadding(tokenizer), compute_metrics=metrics)
    trainer.train()
    results = trainer.evaluate(tokenized["test"])
    predictions = trainer.predict(tokenized["test"])
    predicted = np.argmax(predictions.predictions, axis=1)
    results["per_class"] = classification_report(predictions.label_ids, predicted, target_names=LABELS, output_dict=True, zero_division=0)
    results["confusion_matrix"] = confusion_matrix(predictions.label_ids, predicted).tolist()
    results["labels"] = LABELS
    results["dataset_split"] = {"train": len(dataset["train"]), "validation": len(dataset["val"]), "test": len(dataset["test"])}
    results["base_model"] = args.model
    results["epochs"] = args.epochs
    results["max_length"] = args.max_length
    results["warning"] = "Synthetic development benchmark; not a real-world performance claim."
    trainer.save_model(output)
    tokenizer.save_pretrained(output)
    (output / "evaluation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

