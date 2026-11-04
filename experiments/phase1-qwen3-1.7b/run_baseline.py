#!/usr/bin/env python3
"""Run Qwen3 inference and tokenizer baseline; this script never trains."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import resource
import statistics
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load
from mlx_lm.generate import stream_generate
from mlx_lm.sample_utils import make_sampler


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = EXPERIMENT_DIR / "config.json"
OUTPUTS_PATH = EXPERIMENT_DIR / "baseline_outputs.jsonl"
RESULTS_PATH = EXPERIMENT_DIR / "baseline_results.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _arrays(value: Any):
    if isinstance(value, mx.array):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _arrays(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _arrays(child)


def peak_rss_bytes() -> int:
    # macOS reports ru_maxrss in bytes (Linux reports KiB).
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _read_inputs(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evaluation_path = ROOT / config["evaluation"]["path"]
    manifest_path = ROOT / config["evaluation"]["manifest_path"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["evaluation_frozen"]:
        raise ValueError("This baseline config expects an evaluation set that is not frozen.")
    if manifest["dataset_version"] != config["evaluation"]["expected_dataset_version"]:
        raise ValueError("Dataset version differs from the experiment config.")
    expected_hash = manifest["splits"]["evaluation"]["sha256"]
    if expected_hash != config["evaluation"]["expected_sha256"]:
        raise ValueError("Evaluation SHA-256 differs from the experiment config.")
    manifest_hashes = {
        split: details["sha256"] for split, details in manifest["splits"].items()
    }
    if manifest_hashes != config["dataset_split_sha256"]:
        raise ValueError("Dataset split SHA-256 values differ from the experiment config.")
    actual_hash = sha256_file(evaluation_path)
    if actual_hash != expected_hash:
        raise ValueError("Evaluation file SHA-256 does not match the manifest.")
    records = [
        json.loads(line)
        for line in evaluation_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return records, {
        "dataset_version": manifest["dataset_version"],
        "evaluation_sha256": actual_hash,
        "split_sha256": manifest_hashes,
        "evaluation_size": len(records),
        "evaluation_frozen": manifest["evaluation_frozen"],
    }


def _format_and_validate(
    tokenizer: Any, messages: list[dict[str, str]]
) -> tuple[str, list[int]]:
    rendered = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    token_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    if not tokenizer.has_chat_template:
        raise ValueError("The downloaded tokenizer has no chat template.")
    if "<|im_start|>assistant\n" not in rendered:
        raise ValueError("Official Qwen3 chat template did not append an assistant turn.")
    assistant_suffix = rendered.rsplit("<|im_start|>assistant\n", 1)[-1]
    if assistant_suffix != "<think>\n\n</think>\n\n":
        raise ValueError(
            "The pinned Qwen3 template did not render its expected empty thinking "
            "block for thinking mode off."
        )
    if not token_ids:
        raise ValueError("The formatted conversation tokenized to an empty sequence.")
    return rendered, [int(token_id) for token_id in token_ids]


def _list_lora_candidate_paths(model: Any) -> dict[str, Any]:
    layers = model.model.layers
    suffixes = (
        "self_attn.q_proj",
        "self_attn.k_proj",
        "self_attn.v_proj",
        "self_attn.o_proj",
        "mlp.gate_proj",
        "mlp.up_proj",
        "mlp.down_proj",
    )
    paths = [
        f"model.layers.{index}.{suffix}"
        for index in range(len(layers))
        for suffix in suffixes
    ]
    missing = []
    for index, layer in enumerate(layers):
        modules = (
            ("self_attn.q_proj", layer.self_attn.q_proj),
            ("self_attn.k_proj", layer.self_attn.k_proj),
            ("self_attn.v_proj", layer.self_attn.v_proj),
            ("self_attn.o_proj", layer.self_attn.o_proj),
            ("mlp.gate_proj", layer.mlp.gate_proj),
            ("mlp.up_proj", layer.mlp.up_proj),
            ("mlp.down_proj", layer.mlp.down_proj),
        )
        missing.extend(
            f"model.layers.{index}.{name}"
            for name, module in modules
            if not isinstance(module, nn.Linear)
        )
    if missing:
        raise ValueError(f"Expected Qwen3 Linear target modules were not found: {missing[:5]}")
    return {
        "layer_count": len(layers),
        "candidate_suffixes": list(suffixes),
        "verified_module_count": len(paths),
        "verified_paths": paths,
    }


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    model_path = ROOT / config["model_path"]
    if not (model_path / "config.json").is_file():
        raise FileNotFoundError(f"Model files are not present at {model_path}")

    records, dataset_info = _read_inputs(config)
    rss_before_load = peak_rss_bytes()
    mx.reset_peak_memory()
    model_load_started = time.perf_counter()
    model, tokenizer, model_config = load(
        str(model_path),
        return_config=True,
        trust_remote_code=False,
    )
    parameters = list(_arrays(model.parameters()))
    mx.eval(*parameters)
    model_load_seconds = time.perf_counter() - model_load_started
    mlx_peak_after_load_gb = mx.get_peak_memory() / 1e9
    if not tokenizer.has_chat_template:
        raise ValueError("The downloaded tokenizer has no chat template.")
    if tokenizer.chat_template is None:
        raise ValueError("The downloaded tokenizer has no official chat_template string.")

    tokenizer_checks = []
    prepared_prompts = []
    for record in records:
        messages = record["messages"][:-1]
        rendered, token_ids = _format_and_validate(tokenizer, messages)
        prompt_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        tokenizer_checks.append(
            {
                "record_id": record["id"],
                "token_count": len(token_ids),
                "formatted_prompt_sha256": prompt_hash,
                "thinking_mode": False,
            }
        )
        prepared_prompts.append((record, token_ids, prompt_hash))

    target_modules = _list_lora_candidate_paths(model)
    parameter_dtypes = Counter(str(parameter.dtype) for parameter in parameters)
    parameter_bytes = sum(parameter.nbytes for parameter in parameters)
    sampler = make_sampler(temp=config["generation"]["temperature"])
    mx.random.seed(config["generation"]["seed"])

    warmup_record = records[0]
    warmup_messages = warmup_record["messages"][:-1]
    warmup_messages[-1] = {
        "role": "user",
        "content": "Reply with the single word ready.",
    }
    _, warmup_tokens = _format_and_validate(tokenizer, warmup_messages)
    warmup_started = time.perf_counter()
    for _ in stream_generate(
        model,
        tokenizer,
        warmup_tokens,
        max_tokens=config["generation"]["warmup_max_tokens"],
        sampler=sampler,
    ):
        pass
    warmup_seconds = time.perf_counter() - warmup_started

    generation_results = []
    generation_tps = []
    total_generated_tokens = 0
    total_end_to_end_seconds = 0.0
    mx.reset_peak_memory()
    with OUTPUTS_PATH.open("w", encoding="utf-8") as outputs_file:
        for record, token_ids, prompt_hash in prepared_prompts:
            started = time.perf_counter()
            text_parts = []
            last_response = None
            for last_response in stream_generate(
                model,
                tokenizer,
                token_ids,
                max_tokens=config["generation"]["max_tokens"],
                sampler=sampler,
            ):
                text_parts.append(last_response.text)
            elapsed = time.perf_counter() - started
            if last_response is None:
                raise RuntimeError(f"No generation result for {record['id']}")

            generated_text = "".join(text_parts)
            generated_tokens = last_response.generation_tokens
            total_generated_tokens += generated_tokens
            total_end_to_end_seconds += elapsed
            generation_tps.append(last_response.generation_tps)
            result = {
                "record_id": record["id"],
                "category": record["metadata"]["category"],
                "language": record["metadata"]["language"],
                "formatted_prompt_sha256": prompt_hash,
                "prompt_tokens": last_response.prompt_tokens,
                "prompt_processing_tokens_per_second": last_response.prompt_tps,
                "generated_tokens": generated_tokens,
                "generation_tokens_per_second": last_response.generation_tps,
                "end_to_end_seconds": elapsed,
                "finish_reason": last_response.finish_reason,
                "assistant_output": generated_text,
            }
            outputs_file.write(json.dumps(result, ensure_ascii=False) + "\n")
            outputs_file.flush()
            generation_results.append(
                {
                    key: value
                    for key, value in result.items()
                    if key != "assistant_output"
                }
            )

    # Confirm the held-out input was neither modified nor silently rehashed.
    _, final_dataset_info = _read_inputs(config)
    if final_dataset_info != dataset_info:
        raise RuntimeError("Evaluation file or manifest changed during the baseline run.")

    eval_tps = total_generated_tokens / total_end_to_end_seconds
    dtypes = sorted(parameter_dtypes.items())
    metadata = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "experiment_id": config["experiment_id"],
        "model_id": config["model_id"],
        "model_revision": config["model_revision"],
        "model_path": str(model_path.relative_to(ROOT)),
        "model_config": {
            key: model_config.get(key)
            for key in (
                "model_type",
                "architectures",
                "hidden_size",
                "num_hidden_layers",
                "num_attention_heads",
                "num_key_value_heads",
                "torch_dtype",
            )
        },
        "tokenizer": {
            "revision": config["model_revision"],
            "chat_template_sha256": hashlib.sha256(
                tokenizer.chat_template.encode("utf-8")
            ).hexdigest(),
            "special_tokens": {
                name: {
                    "token": getattr(tokenizer, f"{name}_token", None),
                    "token_id": getattr(tokenizer, f"{name}_token_id", None),
                }
                for name in ("bos", "eos", "pad", "unk")
            },
            "prompt_checks": tokenizer_checks,
        },
        "architecture_lora_module_inspection": target_modules,
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "macos_version": platform.mac_ver()[0],
            "machine": platform.machine(),
            "versions": {
                package: importlib.metadata.version(package)
                for package in ("mlx-lm", "mlx", "mlx-metal", "huggingface-hub", "transformers", "tokenizers")
            },
        },
        "generation": config["generation"],
        "quantization": "No explicit quantization; original Hub safetensors loaded by MLX-LM.",
        "dataset": dataset_info,
        "measurements": {
            "model_load_seconds": model_load_seconds,
            "warmup_seconds_excluded_from_evaluation": warmup_seconds,
            "evaluation_generated_tokens": total_generated_tokens,
            "evaluation_end_to_end_tokens_per_second": eval_tps,
            "median_decode_tokens_per_second": statistics.median(generation_tps),
            "peak_mlx_memory_during_load_gb": mlx_peak_after_load_gb,
            "peak_mlx_memory_during_evaluation_gb": mx.get_peak_memory() / 1e9,
            "peak_mlx_memory_gb": max(
                mlx_peak_after_load_gb, mx.get_peak_memory() / 1e9
            ),
            "process_peak_rss_bytes": peak_rss_bytes(),
            "process_peak_rss_delta_from_preload_bytes": max(
                0, peak_rss_bytes() - rss_before_load
            ),
            "model_parameter_bytes": parameter_bytes,
            "model_parameter_dtypes": dict(dtypes),
        },
        "per_prompt_metrics": generation_results,
        "training_started": False,
        "evaluation_frozen": dataset_info["evaluation_frozen"],
    }
    RESULTS_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "results": str(RESULTS_PATH.relative_to(ROOT)),
                "outputs": str(OUTPUTS_PATH.relative_to(ROOT)),
                "model_load_seconds": model_load_seconds,
                "evaluation_end_to_end_tokens_per_second": eval_tps,
                "peak_mlx_memory_gb": metadata["measurements"]["peak_mlx_memory_gb"],
                "evaluation_size": len(records),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
