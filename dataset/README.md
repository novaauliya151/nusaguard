# NusaGuard dataset

`processed/nusaguard_balanced_synthetic.csv` contains 3,600 deterministic synthetic examples: 600 for each of the six proposal categories. It includes short neutral hard cases and contemporary scam patterns alongside the original templates. It includes explicit provenance and review fields:

- `Provenance=synthetic_template_v1` or `synthetic_contemporary_v2`
- `Synthetic=true`
- `Reviewed=false`
- `Subtipe` and `Template_ID` for auditability

The generated links use the reserved `.invalid` domain or visible placeholders. No operational malicious URL, real credential, or personal identifier is included.

The contemporary hard cases are synthetic paraphrases informed by public safety advisories about APK/package impersonation, fake government updates and QR codes, official impersonation, and AI-assisted voice impersonation. They are not copied victim messages:

- https://www.komdigi.go.id/berita/artikel/detail/waspadai-sniffing-modus-pembobolan-rekening-lewat-whatsapp
- https://www.komdigi.go.id/berita/berita-hoaks/detail/hoaks-surat-edaran-pesan-whatsapp-tautan-dan-barcode-mengatasnamakan-dukcapil-kemendagri
- https://www.komdigi.go.id/berita/berita-komdigi/detail/ini-hoaks-whatsapp-atas-namakan-pj-bupati-takalar

Regenerate the master data and balanced 70/15/15 splits with:

```bash
node dataset/generate_balanced_synthetic.mjs
```

Expected distribution:

| Category | Master | Train | Validation | Test |
|---|---:|---:|---:|---:|
| Aman | 600 | 420 | 90 | 90 |
| Phishing/Link Berbahaya | 600 | 420 | 90 | 90 |
| Social Engineering | 600 | 420 | 90 | 90 |
| Penipuan Investasi | 600 | 420 | 90 | 90 |
| Penipuan Rekrutmen | 600 | 420 | 90 | 90 |
| Penipuan Romansa | 600 | 420 | 90 | 90 |

## Evaluation warning

Synthetic template variants can share linguistic patterns across splits and can make accuracy look unrealistically high. Use this dataset to develop the pipeline and balance classes, not as the sole evidence of real-world performance. Before publishing model metrics:

1. manually review representative samples and set `Reviewed=true` only after review;
2. add consented and anonymized real examples;
3. create an independently curated held-out test set with no template-family overlap;
4. report per-class precision, recall, F1, macro-F1, and the confusion matrix—not accuracy alone.

