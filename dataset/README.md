# NusaGuard dataset

`processed/nusaguard_balanced_synthetic.csv` contains 3,000 deterministic synthetic examples: 500 for each of the six proposal categories. It includes explicit provenance and review fields:

- `Provenance=synthetic_template_v1`
- `Synthetic=true`
- `Reviewed=false`
- `Subtipe` and `Template_ID` for auditability

The generated links use the reserved `.invalid` domain or visible placeholders. No operational malicious URL, real credential, or personal identifier is included.

Regenerate the master data and balanced 70/15/15 splits with:

```bash
node dataset/generate_balanced_synthetic.mjs
```

Expected distribution:

| Category | Master | Train | Validation | Test |
|---|---:|---:|---:|---:|
| Aman | 500 | 350 | 75 | 75 |
| Phishing/Link Berbahaya | 500 | 350 | 75 | 75 |
| Social Engineering | 500 | 350 | 75 | 75 |
| Penipuan Investasi | 500 | 350 | 75 | 75 |
| Penipuan Rekrutmen | 500 | 350 | 75 | 75 |
| Penipuan Romansa | 500 | 350 | 75 | 75 |

## Evaluation warning

Synthetic template variants can share linguistic patterns across splits and can make accuracy look unrealistically high. Use this dataset to develop the pipeline and balance classes, not as the sole evidence of real-world performance. Before publishing model metrics:

1. manually review representative samples and set `Reviewed=true` only after review;
2. add consented and anonymized real examples;
3. create an independently curated held-out test set with no template-family overlap;
4. report per-class precision, recall, F1, macro-F1, and the confusion matrix—not accuracy alone.
