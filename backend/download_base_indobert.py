"""
download_base_indobert.py

Download model IndoBERT DASAR (belum di-fine-tune) buat testing jalur
teknis predictor.py -> endpoint /api/analyze.

PENTING: Model ini belum dilatih untuk klasifikasi 6 kategori NusaGuard.
Kepala klasifikasinya masih ACAK (random weights), jadi hasil prediksi
kategori/confidence BELUM AKURAT. Ini cuma untuk mastiin jalur teknis
(load model -> inference -> response) sudah nyambung dengan benar.

Untuk hasil klasifikasi yang benar, tetap perlu jalankan training
(backend/training/train_indobert.py) dengan dataset asli.

Jalankan dari folder backend/:
    python download_base_indobert.py
"""

from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "indobenchmark/indobert-base-p2"

# 6 kategori NusaGuard, urutan harus konsisten dengan yang dipakai di
# schemas.py / nseae.py / dataset preprocessing
LABELS = [
    "Aman",
    "Phishing/Link Berbahaya",
    "Social Engineering",
    "Penipuan Investasi",
    "Penipuan Rekrutmen",
    "Penipuan Romansa",
]

# Sesuaikan kalau predictor.py kamu pakai path lain
# (cek variabel NUSAGUARD_MODEL_PATH / settings.MODEL_DIR di predictor.py)
SAVE_DIR = Path(__file__).parent / "model" / "indobert"

id2label = {i: label for i, label in enumerate(LABELS)}
label2id = {label: i for i, label in enumerate(LABELS)}

print(f"Downloading tokenizer dari {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print(f"Downloading model dasar dari {MODEL_NAME}...")
print("(kepala klasifikasi akan di-random-init untuk 6 label - normal, belum akurat)")
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABELS),
    id2label=id2label,
    label2id=label2id,
)

SAVE_DIR.mkdir(parents=True, exist_ok=True)
tokenizer.save_pretrained(SAVE_DIR)
model.save_pretrained(SAVE_DIR)

print(f"\nSelesai. Model dan tokenizer tersimpan di: {SAVE_DIR}")
print("INGAT: ini model belum di-fine-tune, hasil klasifikasi belum akurat.")
print("Cukup untuk test jalur teknis predictor.py -> endpoint /api/analyze.")