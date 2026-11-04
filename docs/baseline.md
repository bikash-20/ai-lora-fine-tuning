# Phase 1 baseline report

**Status:** Not run. Awaiting explicit approval before downloading either model or tokenizer files.

The primary machine reports 23 GiB free of 228 GiB available to the current filesystem (89% used). No files larger than 1 MiB were found in this project workspace. The Hugging Face cache check found neither candidate model cached. No model weights, tokenizer files, or packages were downloaded or installed; an empty Python 3.12.13 venv was created locally.

## Candidate metadata

| Candidate | Official revision observed | License / access | Status |
|---|---|---|---|
| `Qwen/Qwen3-1.7B` | `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | Apache-2.0, according to the official model repository metadata and license file. | Not downloaded; benchmark pending |
| `google/gemma-3-1b-it` | `dcc83ea841ab6100d6b47a070329e1ba4cf78752` | Gemma Terms of Use; official model metadata marks the repository gated. Review and accept its terms before access or redistribution. | Not downloaded; benchmark pending |

## Runtime compatibility

The official PyPI metadata for `mlx-lm` 0.32.2 (released 2026-10-16) declares Python 3.11, 3.12, and 3.13 classifiers, but no Python 3.14 classifier. Therefore Python 3.14.2 support is **not declared and is unverified by execution**. `uv` already had CPython 3.12.13 available locally, so an empty project `.venv` was created with that supported interpreter. No packages were installed in it.

The official MLX-LM documentation describes supported Hub models generally but does not confirm the exact Qwen3 and Gemma 3 architectures for the selected release. Architecture support is **not verified**. At Phase 1, check official release-specific model implementations, and test prompt formatting/chat-template/tokenizer behavior only after approval. No tokenizer-only download has been made; the tokenizer revision and special tokens remain unknown pending that approval.

## Benchmark results

| Model revision | Runtime version | Quantization | Load time | Tokens/sec | Peak memory | Quality notes |
|---|---|---|---:|---:|---:|---|
| Qwen `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | Not run | Not run | Not run | Not run | Not run | Requires approved model/tokenizer download |
| Gemma `dcc83ea841ab6100d6b47a070329e1ba4cf78752` | Not run | Not run | Not run | Not run | Not run | Requires gated access and approved model/tokenizer download |

When authorized, run both against the same frozen evaluation prompts, record actual runtime/tokenizer/model revisions and generation settings, and measure load time, generation speed, and peak memory. Do not infer metrics from model size or package documentation.

## Official sources opened

- [MLX-LM 0.32.2 PyPI metadata](https://pypi.org/pypi/mlx-lm/0.32.2/json)
- [MLX-LM official README](https://github.com/ml-explore/mlx-lm/blob/main/README.md)
- [Qwen3-1.7B official model page and metadata](https://huggingface.co/Qwen/Qwen3-1.7B)
- [Qwen3-1.7B official Apache-2.0 license file](https://huggingface.co/Qwen/Qwen3-1.7B/raw/main/LICENSE)
- [Gemma 3 1B IT official model page and metadata](https://huggingface.co/google/gemma-3-1b-it)
- [Google Gemma Terms of Use](https://ai.google.dev/gemma/terms)
- [Google Gemma model documentation](https://ai.google.dev/gemma/docs/core)
