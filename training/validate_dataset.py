#!/usr/bin/env python3
"""Validate generated JSONL splits, provenance, leakage, and near-duplicates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from training.prepare_dataset import (  # noqa: E402
    find_near_duplicates,
    sha256_file,
    validate_no_leakage,
    validate_records,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number} is an empty JSONL line")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {error}") from error
            records.append(record)
    return records


def validate_directory(data_dir: Path, near_duplicate_threshold: float = 0.88) -> dict[str, int]:
    split_filenames = {
        "training": "bikash_ai_train.jsonl",
        "validation": "bikash_ai_validation.jsonl",
        "evaluation": "identity_eval.jsonl",
    }
    splits = {
        name: load_jsonl(data_dir / name / split_filenames[name])
        for name in ("training", "validation", "evaluation")
    }
    for split_name, records in splits.items():
        validate_records(records, split_name)
    validate_no_leakage(splits)
    all_records = [record for rows in splits.values() for record in rows]
    duplicate_pairs = find_near_duplicates(all_records, near_duplicate_threshold)
    if duplicate_pairs:
        details = ", ".join(
            f"{left}/{right} ({score:.2f})" for left, right, score in duplicate_pairs
        )
        raise ValueError(f"Possible near-duplicate prompts: {details}")

    manifest_path = data_dir / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for split_name, records in splits.items():
        expected = manifest["splits"][split_name]
        split_path = data_dir / split_name / split_filenames[split_name]
        if expected["size"] != len(records) or expected["sha256"] != sha256_file(split_path):
            raise ValueError(f"{split_name} does not match the dataset manifest")
    return {name: len(records) for name, records in splits.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--near-duplicate-threshold", type=float, default=0.88)
    args = parser.parse_args()
    sizes = validate_directory(args.data_dir.resolve(), args.near_duplicate_threshold)
    print("JSONL schema, Unicode, duplicate, leakage, near-duplicate, and hash checks passed.")
    print(", ".join(f"{name}={size}" for name, size in sizes.items()))


if __name__ == "__main__":
    main()
