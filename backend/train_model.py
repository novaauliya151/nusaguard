import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
import torch

MODEL_NAME = "indobenchmark/indobert-base-p1"
DATA_PATH = "dataset/processed/labeled.csv"
OUTPUT_DIR = "backend/app/model/indobert"

# ============================================================
# 1. LOAD & SPLIT DATA
# ============================================================

df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["pesan", "kategori_nusaguard"])

labels = sorted(df["kategori_nusaguard"].unique())
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for label, i in label2id.items()}

df["label"] = df["kategori_nusaguard"].map(label2id)

train_df, test_df = train_test_split(
    df, test_size=0.2, random_state=42, stratify=df["label"]
)

print(f"Train: {len(train_df)} | Test: {len(test_df)}")
print(f"Label mapping: {label2id}")

# ============================================================
# 2. TOKENISASI
# ============================================================

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_fn(batch):
    return tokenizer(batch["pesan"], truncation=True, padding="max_length", max_length=128)

train_ds = Dataset.from_pandas(train_df[["pesan", "label"]].reset_index(drop=True))
test_ds = Dataset.from_pandas(test_df[["pesan", "label"]].reset_index(drop=True))

train_ds = train_ds.map(tokenize_fn, batched=True)
test_ds = test_ds.map(tokenize_fn, batched=True)

# ============================================================
# 3. LOAD MODEL
# ============================================================

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id,
)

# ============================================================
# 4. TRAINING
# ============================================================

def compute_metrics(eval_pred):
    logits, y_true = eval_pred
    y_pred = logits.argmax(axis=-1)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, average="macro"),
    }

training_args = TrainingArguments(
    output_dir="backend/train_output",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    logging_steps=10,
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    compute_metrics=compute_metrics,
)

trainer.train()

# ============================================================
# 5. EVALUASI FINAL + SIMPAN MODEL
# ============================================================

pred_output = trainer.predict(test_ds)
y_pred = pred_output.predictions.argmax(axis=-1)
y_true = pred_output.label_ids

print("\n=== Classification Report ===")
print(classification_report(y_true, y_pred, target_names=labels))

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"\nModel tersimpan di {OUTPUT_DIR}")