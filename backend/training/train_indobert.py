import argparse
import json
from pathlib import Path

import numpy as np
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, Trainer, TrainingArguments

LABELS = ["Aman", "Phishing/Link Berbahaya", "Social Engineering", "Penipuan Investasi", "Penipuan Rekrutmen", "Penipuan Romansa"]
LABEL2ID = {label: index for index, label in enumerate(LABELS)}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="indobenchmark/indobert-base-p1")
    parser.add_argument("--data", default="../dataset/training")
    parser.add_argument("--output", default="model/indobert")
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    data_dir, output = (root / args.data).resolve(), (root / "backend" / args.output).resolve()
    dataset = load_dataset("csv", data_files={split: str(data_dir / f"{split}.csv") for split in ("train", "val", "test")})
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    def tokenize(batch):
        encoded = tokenizer(batch["Pesan"], truncation=True, max_length=256)
        encoded["labels"] = [LABEL2ID[label] for label in batch["Kategori_NusaGuard"]]
        return encoded
    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset["train"].column_names)
    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL2ID)
    def metrics(prediction):
        predicted = np.argmax(prediction.predictions, axis=1)
        return {"accuracy": accuracy_score(prediction.label_ids, predicted), "f1_macro": f1_score(prediction.label_ids, predicted, average="macro")}
    trainer = Trainer(model=model, args=TrainingArguments(output_dir=str(output), num_train_epochs=args.epochs, learning_rate=2e-5, per_device_train_batch_size=8, per_device_eval_batch_size=16, eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True, metric_for_best_model="f1_macro", report_to="none", seed=42), train_dataset=tokenized["train"], eval_dataset=tokenized["val"], processing_class=tokenizer, data_collator=DataCollatorWithPadding(tokenizer), compute_metrics=metrics)
    trainer.train()
    results = trainer.evaluate(tokenized["test"])
    trainer.save_model(output)
    tokenizer.save_pretrained(output)
    (output / "evaluation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
