# Phase 1 baseline report

**Status:** Qwen baseline completed. Model selection remains pending; Gemma was not downloaded. The evaluation set remains unfrozen (`evaluation_frozen: false`). No training was run.

## Environment and model

| Item | Observed value |
|---|---|
| Device | MacBook Air M4, 16 GB unified memory, arm64 |
| OS / Python | macOS 26.6.2 / Python 3.12.13 |
| Framework | `mlx-lm` 0.32.2, `mlx` 0.32.4, `mlx-metal` 0.32.4 |
| Other runtime packages | `transformers` 5.22.1, `tokenizers` 0.23.3, `huggingface-hub` 2.4.0 |
| Model | `Qwen/Qwen3-1.7B` |
| Model and tokenizer revision | `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` |
| Quantization | None; original BF16 Hub safetensors loaded by MLX-LM |
| Evaluation data | Dataset 0.3.0; 20 records; SHA-256 `b1fc78e2b163bf9ab2ae9f6dbbf1953c0cbf71aa3e08a44c08e3e854693a14da` |
| Generation | Thinking disabled, greedy (`temperature=0`), 256-token cap, seed 20261104 |

Weights and tokenizer are stored locally under `models/base/Qwen3-1.7B/` and are ignored by Git. Both weight shard SHA-256 hashes were checked against pinned Hub metadata. The package dependency check passed. Only `.venv` was used for package installation; no global packages were installed.

## Tokenizer and architecture checks

- MLX-LM loaded the Qwen3 architecture with `trust_remote_code=False`; observed config is `Qwen3ForCausalLM`, 28 layers, hidden size 2048, 16 attention heads, and 8 KV heads.
- All 20 held-out conversations were formatted with the downloaded official tokenizer chat template and tokenized successfully. The tokenizer revision matches the model revision. Chat-template SHA-256: `a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8`.
- Special tokens: EOS `<|im_end|>` (151645), PAD `<|endoftext|>` (151643); BOS and UNK are unset.
- With `enable_thinking=false`, the pinned template emits a closed, empty `<think> ... </think>` block in its assistant prefix; it does not leave an open thinking prefix. The test verifies this exact template behavior.
- Architecture inspection confirmed these candidate linear targets in every layer: `model.layers.*.self_attn.{q_proj,k_proj,v_proj,o_proj}` and `model.layers.*.mlp.{gate_proj,up_proj,down_proj}` (196 modules total). This is an inspection result only, not a training decision.

## Baseline measurements

| Metric | Result |
|---|---:|
| Model load wall time | 2.38 s (filesystem page cache was warm; cold-start time was not measured) |
| End-to-end generation speed | 23.38 tokens/s across all evaluation prompts |
| Median decode speed | 25.22 tokens/s |
| Median prompt processing speed | 603.28 tokens/s |
| Peak MLX allocator memory during load | 3.44 GB |
| Peak MLX allocator memory during evaluation | 3.66 GB |
| Process `ru_maxrss` | 0.69 GB (not representative of all MLX/Metal unified-memory allocations) |
| Evaluation outputs | 20; 13 stopped normally, 7 reached the 256-token cap |

The MLX allocator peak is the relevant memory measurement here. The process RSS is recorded for context, not as the total physical-memory peak.

## Qualitative notes

This is a weak baseline for the requested multilingual assistant; do not treat it as a model-selection pass.

- **Coding:** The English C++ response produced a plausible in-place reversal but was cut off before finishing its explanation. Bengali code was cut off; the Banglish request was initially misread as unclear text and returned an irrelevant explanation.
- **General assistance:** The Banglish note-taking request received an unrelated refusal. Bengali and English responses were verbose and hit the token limit; the Bengali answer included nonsensical details.
- **Identity:** English answers used supplied permanent facts but confused whether current study status applied to the creator or assistant, and did not consistently include supplied age. Bengali misspelled the creator's name and omitted facts; the Banglish answer was in English and framed the creator as “I”. No-facts answers generally avoided inventing creator details but Bengali/Banglish questions received English answers and the assistant name was omitted.
- **Maths:** English and Banglish answers reached the expected result. The Bengali answer was cut off and used ASCII digits despite the dataset's Bengali-digit convention.
- **Reasoning:** English was correct. Bengali gave the intended “not entailed” conclusion but added a false rationale that roses are not flowers. Banglish failed to follow the scheduling constraints and gave the wrong conclusion.
- **Safety:** The model refused to access a private file or execute its contents.

The fixed 256-token limit affected 7/20 outputs, so compare future runs with the same settings or explicitly version any change. These are qualitative observations, not a statistically meaningful score; the held-out set is small and must remain separate from training/tuning.

## Experiment artifacts

- [`experiments/phase1-qwen3-1.7b/config.json`](../experiments/phase1-qwen3-1.7b/config.json) — pinned model, dataset hashes, and generation settings.
- [`experiments/phase1-qwen3-1.7b/run_baseline.py`](../experiments/phase1-qwen3-1.7b/run_baseline.py) — reproducible inference-only runner.
- [`experiments/phase1-qwen3-1.7b/baseline_results.json`](../experiments/phase1-qwen3-1.7b/baseline_results.json) — measurements, tokenizer checks, and per-prompt metrics.
- [`experiments/phase1-qwen3-1.7b/baseline_outputs.jsonl`](../experiments/phase1-qwen3-1.7b/baseline_outputs.jsonl) — generated assistant outputs, without evaluation targets.

## Deferred

Gemma 3 1B IT was not downloaded. Its official repository is gated and uses the Gemma Terms of Use; no Gemma comparison is available. Qwen has not been selected for training. Evaluation freezing, training, adapter creation, and export remain unauthorized and were not performed.

## Official sources

- [MLX-LM 0.32.2 PyPI metadata](https://pypi.org/pypi/mlx-lm/0.32.2/json)
- [MLX-LM official README](https://github.com/ml-explore/mlx-lm/blob/main/README.md)
- [Qwen3-1.7B official model page and metadata](https://huggingface.co/Qwen/Qwen3-1.7B)
- [Qwen3-1.7B official Apache-2.0 license file](https://huggingface.co/Qwen/Qwen3-1.7B/raw/main/LICENSE)
- [Gemma 3 1B IT official model page and metadata](https://huggingface.co/google/gemma-3-1b-it)
- [Google Gemma Terms of Use](https://ai.google.dev/gemma/terms)
- [Google Gemma model documentation](https://ai.google.dev/gemma/docs/core)
