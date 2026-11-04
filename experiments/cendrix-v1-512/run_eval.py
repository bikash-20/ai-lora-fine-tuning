#!/usr/bin/env python3
"""Reproduce the 512-token inference-only evaluation without changing its input."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import statistics
import sys
import time
from pathlib import Path
from typing import Any

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import stream_generate
from mlx_lm.sample_utils import make_sampler


EXPERIMENT_DIR = Path(__file__).resolve().parent
CONFIG = json.loads((EXPERIMENT_DIR / "config.json").read_text(encoding="utf-8"))
RESULTS_PATH = EXPERIMENT_DIR / "results.json"
OUTPUTS_PATH = EXPERIMENT_DIR / "outputs.jsonl"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    dataset_path = ROOT / CONFIG["evaluation"]["path"]
    actual_hash = sha256_file(dataset_path)
    if actual_hash != CONFIG["evaluation"]["sha256"]:
        raise ValueError("Evaluation input hash changed; refusing to run.")
    records = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    model_path = ROOT / CONFIG["model_path"]
    if not (model_path / "config.json").is_file():
        raise FileNotFoundError(f"Local model is missing: {model_path}")

    before_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    mx.reset_peak_memory()
    load_start = time.perf_counter()
    model, tokenizer = load(str(model_path), trust_remote_code=False)
    mx.eval(model.parameters())
    load_seconds = time.perf_counter() - load_start
    load_peak_gb = mx.get_peak_memory() / 1e9
    if not tokenizer.has_chat_template or tokenizer.chat_template is None:
        raise ValueError("The downloaded tokenizer has no official chat template.")

    sampler = make_sampler(temp=CONFIG["generation"]["temperature"])
    mx.random.seed(CONFIG["generation"]["seed"])
    warmup_messages = records[0]["messages"][:-1]
    warmup_messages[-1] = {
        "role": "user",
        "content": "Reply with the single word ready.",
    }
    warmup_prompt = tokenizer.apply_chat_template(
        warmup_messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    warmup_start = time.perf_counter()
    for _ in stream_generate(
        model, tokenizer, warmup_prompt, max_tokens=24, sampler=sampler
    ):
        pass
    warmup_seconds = time.perf_counter() - warmup_start

    generated_total = 0
    elapsed_total = 0.0
    decode_rates: list[float] = []
    generation_results: list[dict[str, Any]] = []
    mx.reset_peak_memory()
    with OUTPUTS_PATH.open("w", encoding="utf-8") as output_file:
        for record in records:
            messages = record["messages"][:-1]
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            started = time.perf_counter()
            parts: list[str] = []
            last_response = None
            for last_response in stream_generate(
                model,
                tokenizer,
                prompt,
                max_tokens=CONFIG["generation"]["max_tokens"],
                sampler=sampler,
            ):
                parts.append(last_response.text)
            elapsed = time.perf_counter() - started
            if last_response is None:
                raise RuntimeError(f"No response generated for {record['id']}.")
            text = "".join(parts)
            generated_total += last_response.generation_tokens
            elapsed_total += elapsed
            decode_rates.append(last_response.generation_tps)
            result = {
                "record_id": record["id"],
                "category": record["metadata"]["category"],
                "language": record["metadata"]["language"],
                "generated_tokens": last_response.generation_tokens,
                "finish_reason": last_response.finish_reason,
                "generation_tokens_per_second": last_response.generation_tps,
                "end_to_end_seconds": elapsed,
                "assistant_output": text,
            }
            output_file.write(json.dumps(result, ensure_ascii=False) + "\n")
            generation_results.append(
                {key: value for key, value in result.items() if key != "assistant_output"}
            )

    final_hash = sha256_file(dataset_path)
    if final_hash != actual_hash:
        raise RuntimeError("Evaluation file changed during run.")
    eval_peak_gb = mx.get_peak_memory() / 1e9
    max_tokens = CONFIG["generation"]["max_tokens"]
    limit_hits = sum(
        result["generated_tokens"] >= max_tokens
        or result["finish_reason"] == "length"
        for result in generation_results
    )
    output = {
        "experiment_id": CONFIG["experiment_id"],
        "model_id": CONFIG["model_id"],
        "model_revision": CONFIG["model_revision"],
        "model_path": CONFIG["model_path"],
        "quantization": CONFIG["generation"]["quantization"],
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "mlx_lm": importlib.metadata.version("mlx-lm"),
            "mlx": importlib.metadata.version("mlx"),
            "mlx_metal": importlib.metadata.version("mlx-metal"),
        },
        "tokenizer": {
            "revision": CONFIG["model_revision"],
            "chat_template_sha256": hashlib.sha256(
                tokenizer.chat_template.encode("utf-8")
            ).hexdigest(),
            "thinking_mode": False,
        },
        "dataset": {
            "path": CONFIG["evaluation"]["path"],
            "sha256": actual_hash,
            "records": len(records),
            "evaluation_frozen": False,
        },
        "generation": CONFIG["generation"],
        "measurements": {
            "model_load_seconds": load_seconds,
            "warmup_seconds_excluded": warmup_seconds,
            "end_to_end_tokens_per_second": generated_total / elapsed_total,
            "median_decode_tokens_per_second": statistics.median(decode_rates),
            "peak_mlx_memory_during_load_gb": load_peak_gb,
            "peak_mlx_memory_during_eval_gb": eval_peak_gb,
            "peak_mlx_memory_gb": max(load_peak_gb, eval_peak_gb),
            "process_peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "process_peak_rss_delta_from_preload_bytes": max(
                0,
                int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) - before_rss,
            ),
            "evaluation_generated_tokens": generated_total,
            "max_token_limit_hits": limit_hits,
            "max_token_limit": max_tokens,
        },
        "per_prompt_metrics": generation_results,
        "training_started": False,
        "evaluation_frozen": False,
    }
    RESULTS_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output["measurements"], indent=2))


if __name__ == "__main__":
    main()
