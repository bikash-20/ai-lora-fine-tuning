# Reproducible experiments

The inference-only Qwen3 Phase 1 baseline is recorded in [`phase1-qwen3-1.7b/`](./phase1-qwen3-1.7b/). It uses the pinned base model and held-out evaluation hash, and does not train or freeze evaluation. No training experiment has been run.

For each future experiment, keep a separate directory with:

- `config.json` or `config.yaml`: base model ID and revision, dataset version and split hashes, runtime/framework versions, training parameters, and random seed.
- `logs/`: captured training and evaluation output.
- `metrics.json`: validation loss and per-task quality metrics.
- `report.md`: final comparison against the unchanged base-model baseline, including regressions and checkpoint disposition.
- `checkpoints/`: local-only artifacts, ignored by Git.

Do not start training before explicit approval. Keep the base model outside experiment outputs and save LoRA adapters separately.
