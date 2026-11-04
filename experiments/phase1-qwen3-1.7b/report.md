# Qwen3-1.7B Phase 1 baseline

Inference-only baseline; no training, quantization, or evaluation freeze.

- Model/tokenizer: `Qwen/Qwen3-1.7B` at `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`.
- Environment: macOS 26.6.2, MacBook Air M4 / 16 GB, Python 3.12.13, `mlx-lm` 0.32.2.
- Dataset: 20 evaluation prompts, dataset 0.3.0, evaluation SHA-256 `b1fc78e2b163bf9ab2ae9f6dbbf1953c0cbf71aa3e08a44c08e3e854693a14da`; evaluation remains unfrozen.
- Template: official Qwen3 chat template; thinking disabled; all 20 prompts tokenized successfully.
- Candidate LoRA modules verified in the architecture: `model.layers.*.self_attn.{q_proj,k_proj,v_proj,o_proj}` and `model.layers.*.mlp.{gate_proj,up_proj,down_proj}` (196 modules).
- Performance: 2.38 s model load with warm filesystem cache; 23.38 end-to-end tokens/s; 25.22 median decode tokens/s; 3.66 GB peak MLX allocation.
- Quality: substantial multilingual/reasoning failures and 7/20 outputs reached the 256-token cap. See [`docs/baseline.md`](../../docs/baseline.md) for category notes and caveats.

Artifacts: [`config.json`](./config.json), [`run_baseline.py`](./run_baseline.py), [`baseline_results.json`](./baseline_results.json), and [`baseline_outputs.jsonl`](./baseline_outputs.jsonl). The outputs file does not include expected evaluation answers.
