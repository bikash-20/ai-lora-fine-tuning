# Cendrix AI v1.0 — local PWA and inference report

**Status:** Local app implemented and smoke-tested with the pinned Qwen3 model. No model download, package install, fine-tuning, evaluation freeze, 4-bit conversion, or Git commit/push was performed in this phase.

## Run locally

From the project directory:

```bash
PYTHONPATH=. .venv/bin/python -m app.run
```

Open `http://127.0.0.1:8765`. The server refuses to bind to any address other than `127.0.0.1`. It loads Qwen3 lazily on the first non-identity question, from `models/base/Qwen3-1.7B/`. The app sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` before MLX-LM is imported.

To check offline operation, first open the local app once so its service worker caches the app shell. Stop the server, turn off Wi-Fi, restart it with the command above, and try a fresh chat with a coding or maths question. The model and tokenizer must already be present locally. The app shell has no external font, script, or API dependency; inference uses the local model. The SQLite database is created at `storage/database/conversations.sqlite3` and is ignored by Git.

The interface is an installable local PWA where the browser supports installation from a loopback origin. It is not deployed to Hugging Face: a hosted app would not provide this local, offline MLX inference path. Hugging Face deployment would be a separate online service decision.

## Identity behavior

The real-model prompt-only check ran all 10 requested English, Bengali, and Banglish questions with the current Cendrix system prompt, the official Qwen3 chat template, thinking disabled, greedy decoding, and a 128-token cap.

| Mode | Result | Notes |
|---|---:|---|
| System prompt only | 3/10 | English “Who created you?”, “Who made Cendrix AI?”, and the legacy-name question passed. |
| Deterministic identity fallback | 10/10 unit checks | Covers all specified question forms and returns localized text from the current identity configuration. The real model is bypassed for these recognized questions. |

The prompt-only failures were:

- English: “Who is your developer?” (volunteered age and current status).
- Bengali: all three requested questions (creator name/language correctness failed).
- Banglish: all three requested questions (refusal, unsolicited dynamic facts, or wrong language).

The pass rubric requires a correct creator name and language, with no unsolicited age or current-status fact. The permanent project-origin fact (built during the creator's second year) is allowed. The fallback includes the age or current status only when its question classifier detects a request for that dynamic fact. Updating `configs/identity.json` changes both the assembled system prompt and fallback answer; no retraining is involved.

## Baseline and English smoke tests

The 512-token evaluation uses the same 20 records and same held-out JSONL as the previous 256-token baseline. It does not modify the evaluation set, and `evaluation_frozen` remains `false`.

| Metric | Previous 256-token baseline | Cendrix 512-token run |
|---|---:|---:|
| Model / revision | Qwen3-1.7B / `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | Same |
| Runtime | MLX-LM 0.32.2 / MLX 0.32.4 | Same |
| Quantization | Original BF16 weights | Original BF16 weights |
| Load time | 2.38 s | 2.19 s |
| End-to-end generation speed | 23.38 tokens/s | 24.73 tokens/s |
| Median decode speed | 25.22 tokens/s | 26.22 tokens/s |
| Peak MLX allocator memory | 3.66 GB | 3.66 GB |
| Outputs reaching token cap | 7/20 at 256 | 2/20 at 512 |

The two remaining 512-token cap hits are Bengali coding (`coding-bn-02`) and Bengali general assistance (`general_assistance-bn-01`). English prompts did not hit the cap. The RSS peak was 2.11 GB in the final run; it does not represent all unified-memory/Metal allocations, so the MLX allocator peak is the relevant memory measurement. Load times were measured with a warm filesystem cache.

An additional real-app smoke test used the new Cendrix system prompt and local HTTP/SQLite path:

- English Python: produced a short addition function with a plain explanation.
- English maths: correctly calculated 3 × 4 = 12.
- Follow-up: correctly recalled the 12-apple result from saved conversation context.
- The runtime returned the assistant output as text only; it has no shell-command or model-directed file-access execution path.

The unchanged held-out English checks also returned plausible C++ reversal code, the correct discounted-and-taxed price ($71.40), the correct reasoning conclusion (70 minutes does not fit in 55), and a refusal to access or execute a private file. Responses can still be verbose; this is a small evaluation set, not evidence of broad English robustness.

## App design and safeguards

- MLX model and tokenizer are local and loaded once, on demand. Missing model, memory exhaustion, and generation failures produce friendly errors.
- Conversation context is limited to the newest 20 messages and at most 16,000 history characters. The database retains conversation history separately.
- SQLite is outside `models/` and `configs/`; database files are Git-ignored.
- The stdlib HTTP server only binds to loopback, caps request size, validates JSON and UUIDs, checks browser origins, and sets a restrictive Content Security Policy.
- Model text is displayed and stored as text. No generated shell commands are executed, and the model has no file tool.
- The UI and service worker make no external network requests. API calls are excluded from service-worker caching.
- Browser verification passed at desktop and 390 px mobile widths, with no horizontal overflow.
- Existing security tests for untrusted prompt content and approved file roots remain in place.

## Reproduce the 512-token evaluation

```bash
PYTHONPATH=. .venv/bin/python experiments/cendrix-v1-512/run_eval.py
```

The run checks the exact evaluation SHA-256 before and after generation. Configuration, per-prompt outputs, measured results, pinned revision, tokenizer-template hash, and runtime metadata are stored under `experiments/cendrix-v1-512/`. The prior Phase 1 baseline files are unchanged.

## Quantization and remaining decisions

No 4-bit copy was created. MLX 4-bit is a distinct format from GGUF `Q4_K_M`; neither should be assumed to match BF16 quality. Creating and measuring an MLX 4-bit copy requires separate approval. No training was started.

The local PWA is the selected v1 deployment target because it matches the offline requirement. A Hugging Face-hosted deployment would be online and requires a separate deployment and privacy decision.
