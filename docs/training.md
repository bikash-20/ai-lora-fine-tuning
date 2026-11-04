# Training plan (not started)

No training or model conversion scripts are included in this phase. Training is blocked until the owner approves the held-out dataset and the Phase 1 model selection.

When approved, use supervised LoRA only, keep base weights untouched, save adapters separately, and record the selected base revision, tokenizer revision, official chat template, model-specific target modules, rank, alpha, dropout, learning rate, batch size, gradient accumulation, epochs, and random seed in an experiment configuration. Compare validation loss and task-level behavior with the baseline; reject checkpoints that regress important capabilities.

Model-specific LoRA targets, tokenizer behavior, prompt formatting, and MLX support have not been verified by execution. Do not use a generic replacement Transformer or begin training until model approval and tokenizer-only download approval are separately obtained.
