"""
dataset/preprocess.py

Alur:
    dataset/raw/*.csv          (Kategori, Pesan, [Kategori_NusaGuard opsional])
        |
        v
    validasi & bersihin
        |
        v
    dataset/processed/nusaguard_clean.csv   (semua baris yang valid & lengkap)
    dataset/processed/needs_review.csv      (baris spam yang belum ada Kategori_NusaGuard)
        |
        v
    dataset/training/train.csv / val.csv / test.csv   (stratified split, siap buat training)

Cara jalanin (dari root nusaguard/):
    cd dataset
    python preprocess.py

Requirement: pandas, scikit-learn
    pip install pandas scikit-learn
"""

import re
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------
# 0. KONFIGURASI — samain dengan enum di backend/app/models/schemas.py
# ---------------------------------------------------------

VALID_KATEGORI = {"spam", "ham"}

VALID_KATEGORI_NUSAGUARD = {
    "Aman",
    "Phishing/Link Berbahaya",
    "Social Engineering",
    "Penipuan Investasi",
    "Penipuan Rekrutmen",
    "Penipuan Romansa",
}

RAW_DIR = Path(__file__).parent / "raw"
PROCESSED_DIR = Path(__file__).parent / "processed"
TRAINING_DIR = Path(__file__).parent / "training"

RANDOM_SEED = 42
TEST_SIZE = 0.15   # 15% buat test
VAL_SIZE = 0.15    # 15% dari sisanya buat validation


# ---------------------------------------------------------
# 1. LOAD semua CSV di dataset/raw/
# ---------------------------------------------------------

def load_raw_csvs() -> pd.DataFrame:
    csv_files = list(RAW_DIR.glob("*.csv"))

    if not csv_files:
        print(f"[ERROR] Tidak ada file .csv di {RAW_DIR}")
        print("        Taruh dataset mentah kamu di dataset/raw/ dulu.")
        sys.exit(1)

    print(f"Ditemukan {len(csv_files)} file CSV di raw/:")
    dfs = []
    for f in csv_files:
        print(f"  - {f.name}")
        df = pd.read_csv(f)
        df["_source_file"] = f.name
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal baris digabung: {len(combined)}")
    return combined


# ---------------------------------------------------------
# 2. NORMALISASI nama kolom
#    (biar nggak error kalau ada yang nulis "kategori" vs "Kategori")
# ---------------------------------------------------------

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        key = col.strip().lower()
        if key == "kategori":
            rename_map[col] = "Kategori"
        elif key == "pesan":
            rename_map[col] = "Pesan"
        elif key in ("kategori_nusaguard", "kategori nusaguard"):
            rename_map[col] = "Kategori_NusaGuard"
    df = df.rename(columns=rename_map)

    required = {"Kategori", "Pesan"}
    missing = required - set(df.columns)
    if missing:
        print(f"[ERROR] Kolom wajib tidak ditemukan: {missing}")
        sys.exit(1)

    if "Kategori_NusaGuard" not in df.columns:
        df["Kategori_NusaGuard"] = pd.NA

    return df


# ---------------------------------------------------------
# 3. BERSIHIN teks pesan
#    NOTE: sengaja tidak menghapus link/nomor telepon/simbol,
#    karena justru itu salah satu fitur penting buat deteksi phishing.
#    Yang dibersihin cuma whitespace berlebih.
# ---------------------------------------------------------

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)   # rapikan spasi/newline berlebih
    return text


# ---------------------------------------------------------
# 4. VALIDASI + AUTO-FILL label
#    - ham tanpa Kategori_NusaGuard -> otomatis "Aman"
#    - spam tanpa Kategori_NusaGuard -> masuk needs_review (butuh label manual)
#    - baris dengan Kategori/Kategori_NusaGuard yang typo -> ditolak, dicatat
# ---------------------------------------------------------

def validate_and_split(df: pd.DataFrame):
    df["Pesan"] = df["Pesan"].apply(clean_text)
    df["Kategori"] = df["Kategori"].astype(str).str.strip().str.lower()
    df["Kategori_NusaGuard"] = df["Kategori_NusaGuard"].apply(
        lambda x: x.strip() if isinstance(x, str) else x
    )

    # buang baris pesan kosong
    before = len(df)
    df = df[df["Pesan"].str.len() > 0].copy()
    if len(df) < before:
        print(f"  Dibuang {before - len(df)} baris karena Pesan kosong")

    # buang baris duplikat (pesan sama persis)
    before = len(df)
    df = df.drop_duplicates(subset=["Pesan"]).copy()
    if len(df) < before:
        print(f"  Dibuang {before - len(df)} baris duplikat")

    # validasi Kategori
    invalid_kategori = df[~df["Kategori"].isin(VALID_KATEGORI)]
    if len(invalid_kategori) > 0:
        print(f"  [WARNING] {len(invalid_kategori)} baris punya Kategori tidak dikenal, dibuang:")
        print(f"            nilai aneh: {invalid_kategori['Kategori'].unique().tolist()}")
        df = df[df["Kategori"].isin(VALID_KATEGORI)].copy()

    # auto-fill: ham tanpa Kategori_NusaGuard -> "Aman"
    ham_kosong = (df["Kategori"] == "ham") & (df["Kategori_NusaGuard"].isna())
    df.loc[ham_kosong, "Kategori_NusaGuard"] = "Aman"
    print(f"  Auto-fill 'Aman' untuk {ham_kosong.sum()} baris ham")

    # pisahkan: spam yang belum punya label spesifik -> needs_review
    needs_review = df[(df["Kategori"] == "spam") & (df["Kategori_NusaGuard"].isna())].copy()
    df = df.drop(needs_review.index)

    # validasi Kategori_NusaGuard yang sudah terisi (tangkap typo)
    filled = df[df["Kategori_NusaGuard"].notna()]
    invalid_label = filled[~filled["Kategori_NusaGuard"].isin(VALID_KATEGORI_NUSAGUARD)]
    if len(invalid_label) > 0:
        print(f"  [WARNING] {len(invalid_label)} baris punya Kategori_NusaGuard tidak dikenal:")
        print(f"            nilai aneh: {invalid_label['Kategori_NusaGuard'].unique().tolist()}")
        print(f"            Cek typo dibanding 6 kategori resmi: {sorted(VALID_KATEGORI_NUSAGUARD)}")
        # baris ini juga dipindah ke needs_review, bukan dibuang, biar bisa dikoreksi manual
        needs_review = pd.concat([needs_review, invalid_label], ignore_index=True)
        df = df.drop(invalid_label.index)

    clean_df = df[["Kategori", "Pesan", "Kategori_NusaGuard"]].reset_index(drop=True)
    review_df = needs_review[["Kategori", "Pesan", "Kategori_NusaGuard"]].reset_index(drop=True)

    return clean_df, review_df


# ---------------------------------------------------------
# 5. SPLIT train / val / test (stratified biar proporsi tiap label rata)
# ---------------------------------------------------------

def split_dataset(df: pd.DataFrame):
    label_counts = df["Kategori_NusaGuard"].value_counts()
    too_few = label_counts[label_counts < 3]
    if len(too_few) > 0:
        print(f"\n[WARNING] Label berikut punya <3 sample, stratified split mungkin gagal:")
        print(too_few)
        print("          Pertimbangkan tambah data untuk label ini sebelum training.")

    train_val, test = train_test_split(
        df,
        test_size=TEST_SIZE,
        stratify=df["Kategori_NusaGuard"],
        random_state=RANDOM_SEED,
    )
    train, val = train_test_split(
        train_val,
        test_size=VAL_SIZE,
        stratify=train_val["Kategori_NusaGuard"],
        random_state=RANDOM_SEED,
    )
    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NusaGuard Dataset Preprocessing")
    print("=" * 60)

    raw_df = load_raw_csvs()
    raw_df = normalize_columns(raw_df)

    print("\nValidasi & pembersihan...")
    clean_df, review_df = validate_and_split(raw_df)

    clean_path = PROCESSED_DIR / "nusaguard_clean.csv"
    clean_df.to_csv(clean_path, index=False)
    print(f"\n✓ {len(clean_df)} baris valid disimpan ke: {clean_path}")

    if len(review_df) > 0:
        review_path = PROCESSED_DIR / "needs_review.csv"
        review_df.to_csv(review_path, index=False)
        print(f"⚠ {len(review_df)} baris BUTUH LABEL MANUAL, disimpan ke: {review_path}")
        print("  Buka file itu, isi kolom Kategori_NusaGuard-nya, lalu pindahkan")
        print("  baris yang sudah dilabel ke dataset/raw/ dan jalankan ulang script ini.")

    print("\nDistribusi label (data valid):")
    print(clean_df["Kategori_NusaGuard"].value_counts())

    if len(clean_df) < 20:
        print("\n[WARNING] Dataset valid masih sangat sedikit untuk split train/val/test.")
        print("          Lengkapi needs_review.csv dulu sebelum lanjut training.")
        return

    print("\nSplitting train/val/test...")
    train, val, test = split_dataset(clean_df)

    train.to_csv(TRAINING_DIR / "train.csv", index=False)
    val.to_csv(TRAINING_DIR / "val.csv", index=False)
    test.to_csv(TRAINING_DIR / "test.csv", index=False)

    print(f"✓ train: {len(train)} baris -> dataset/training/train.csv")
    print(f"✓ val:   {len(val)} baris -> dataset/training/val.csv")
    print(f"✓ test:  {len(test)} baris -> dataset/training/test.csv")

    print("\nSelesai! Lanjut ke training IndoBERT pakai dataset/training/*.csv")


if __name__ == "__main__":
    main()