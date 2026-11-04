# Reproducible experiments

No experiment has been run yet. After the dataset and baseline are approved, create one directory per experiment with:

- `config.json` or `config.yaml`: base model ID and revision, dataset version and split hashes, runtime/framework versions, training parameters, and random seed.
- `logs/`: captured training and evaluation output.
- `metrics.json`: validation loss and per-task quality metrics.
- `report.md`: final comparison against the unchanged base-model baseline, including regressions and checkpoint disposition.
- `checkpoints/`: local-only artifacts, ignored by Git.

Do not start training before explicit approval. Keep the base model outside experiment outputs and save LoRA adapters separately.
