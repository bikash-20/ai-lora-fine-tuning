import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from training.prepare_dataset import (
    build_records,
    build_identity_evaluation_records,
    find_near_duplicates,
    normalized_text,
    split_records,
    validate_no_leakage,
    validate_records,
    validate_training_identity,
)
from training.validate_dataset import load_jsonl, validate_directory


ROOT = Path(__file__).resolve().parents[1]


class DatasetPipelineTests(unittest.TestCase):
    def test_splits_are_deterministic_stratified_and_have_no_prompt_leakage(self) -> None:
        records = build_records()
        splits = split_records(records)
        splits["evaluation"].extend(build_identity_evaluation_records())
        splits["evaluation"].sort(key=lambda row: row["id"])
        validate_no_leakage(splits)
        self.assertEqual(
            {name: len(rows) for name, rows in splits.items()},
            {"training": 27, "validation": 18, "evaluation": 20},
        )
        expected_splits = split_records(records)
        expected_splits["evaluation"].extend(build_identity_evaluation_records())
        expected_splits["evaluation"].sort(key=lambda row: row["id"])
        self.assertEqual(
            {name: [row["id"] for row in rows] for name, rows in splits.items()},
            {
                name: [row["id"] for row in rows]
                for name, rows in expected_splits.items()
            },
        )
        self.assertEqual(validate_training_identity(records), 100 * 3 / 27)
        for rows in splits.values():
            validate_records(rows, "test")

    def test_evaluation_covers_languages_categories_and_identity_facts(self) -> None:
        evaluation = split_records(build_records())["evaluation"]
        evaluation.extend(build_identity_evaluation_records())
        evaluation.sort(key=lambda row: row["id"])
        rows = [row for row in evaluation]
        identity_rows = [row for row in rows if row["metadata"]["category"] == "identity"]
        self.assertEqual(
            {row["metadata"]["language"] for row in identity_rows},
            {"Bengali", "English", "Banglish"},
        )
        self.assertEqual(
            {row["metadata"]["category"] for row in rows},
            {"general_assistance", "coding", "maths", "reasoning", "identity", "safety"},
        )
        en_identity = next(
            row for row in identity_rows
            if row["id"] == "identity-eval-en"
        )
        self.assertEqual(
            en_identity["messages"][2]["content"],
            "I was born by Bikash Talukder, he is a talented AI engineer, 24 years old, currently studying computer science and engineering, he made me in his second year of his computer science journey.",
        )
        no_facts = [
            row for row in identity_rows if row["id"].startswith("identity-eval-no-facts-")
        ]
        self.assertEqual(len(no_facts), 3)
        for row in no_facts:
            self.assertIn("No creator-specific facts are supplied", row["messages"][0]["content"])
            self.assertNotIn("Bikash Talukder", row["messages"][0]["content"])
            self.assertIn("Bikash-AI", row["messages"][0]["content"])
        expected_no_facts_answers = {
            "Bengali": "আমি শুধু জানি যে আমি Bikash-AI। এই প্রসঙ্গে আমার নির্মাতা সম্পর্কে কোনো তথ্য দেওয়া হয়নি।",
            "English": "I only know that I am Bikash-AI; no creator details have been supplied in this context.",
            "Banglish": "Ami shudhu jani je ami Bikash-AI; ei context-e amar creator-er kono details deya hoyni.",
        }
        for row in no_facts:
            self.assertEqual(
                row["messages"][2]["content"],
                expected_no_facts_answers[row["metadata"]["language"]],
            )

    def test_generation_cli_and_manifest_hashes_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "training" / "prepare_dataset.py"),
                    "--output-dir",
                    str(data_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            sizes = validate_directory(data_dir)
            sample = Path(temp_dir) / "docs" / "dataset_review_sample.jsonl"
            sample_rows = load_jsonl(sample)
            manifest = json.loads((data_dir / "dataset_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(sizes, {"training": 27, "validation": 18, "evaluation": 20})
        self.assertEqual(len(sample_rows), 45)
        self.assertEqual(
            {row["metadata"]["language"] for row in sample_rows},
            {"Bengali", "Banglish", "English"},
        )
        self.assertFalse(any(row["id"].startswith("identity-eval") for row in sample_rows))
        self.assertTrue(
            any(row["metadata"]["category"] == "reasoning" for row in sample_rows)
        )
        self.assertTrue(all(not row["metadata"]["reviewed_by_human"] for row in sample_rows))
        self.assertFalse(manifest["evaluation_frozen"])
        self.assertEqual(manifest["identity_share_of_training_percent"], 11.11)
        self.assertTrue(all(details["sha256"] for details in manifest["splits"].values()))
        self.assertEqual(manifest["review_sample"]["size"], 45)
        self.assertEqual(
            manifest["generation_provenance"]["tool"],
            "GitHub Copilot SDK in VS Code assistant session",
        )
        all_records = build_records()
        self.assertTrue(
            all(record["metadata"]["creation_method"] == "ai-generated" for record in all_records)
        )
        self.assertTrue(
            all(
                record["metadata"]["creation_method"] == "ai-generated"
                for record in build_identity_evaluation_records()
            )
        )
        synthetic_identities = [
            record for record in all_records
            if record["metadata"]["category"] == "identity"
        ]
        self.assertTrue(all(record["metadata"]["synthetic_fixture"] for record in synthetic_identities))
        for record in synthetic_identities:
            if record["metadata"]["language"] == "Bengali":
                self.assertNotIn("studying ", record["messages"][2]["content"])
                self.assertNotIn(" built me ", record["messages"][2]["content"])

    def test_normalized_prompt_leakage_is_detected(self) -> None:
        row = build_records()[0]
        duplicate = json.loads(json.dumps(row))
        duplicate["id"] = "different-id"
        duplicate["metadata"]["record_id"] = "different-id"
        duplicate["messages"][1]["content"] = row["messages"][1]["content"].upper()
        with self.assertRaisesRegex(ValueError, "duplicates.*after normalization"):
            validate_records([row, duplicate], "test")
        with self.assertRaisesRegex(ValueError, "leakage"):
            validate_no_leakage({"training": [row], "evaluation": [duplicate]})

    def test_schema_rejects_bad_roles_empty_messages_and_malformed_unicode(self) -> None:
        row = build_records()[0]
        wrong_roles = json.loads(json.dumps(row))
        wrong_roles["messages"][0]["role"] = "user"
        with self.assertRaisesRegex(ValueError, "incorrect conversation roles"):
            validate_records([wrong_roles], "test")

        empty = json.loads(json.dumps(row))
        empty["messages"][1]["content"] = " "
        with self.assertRaisesRegex(ValueError, "empty or not text"):
            validate_records([empty], "test")

        malformed = json.loads(json.dumps(row))
        malformed["messages"][2]["content"] = "\ud800"
        with self.assertRaisesRegex(ValueError, "malformed Unicode"):
            validate_records([malformed], "test")

    def test_invalid_json_and_duplicate_records_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid = Path(temp_dir) / "invalid.jsonl"
            invalid.write_text("{bad json}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                load_jsonl(invalid)

        row = build_records()[0]
        with self.assertRaisesRegex(ValueError, "duplicates record id"):
            validate_records([row, row], "test")

    def test_missing_provenance_fields_are_rejected(self) -> None:
        row = json.loads(json.dumps(build_records()[0]))
        del row["metadata"]["license"]
        with self.assertRaisesRegex(ValueError, "missing provenance metadata"):
            validate_records([row], "test")

    def test_near_duplicate_check_is_separate_and_detects_similar_prompts(self) -> None:
        records = build_records()
        left = next(
            row for row in records
            if row["metadata"]["language"] == "English"
            and row["metadata"]["category"] == "general_assistance"
        )
        right = json.loads(json.dumps(left))
        right["messages"][1]["content"] = "How can I make a realistic seven-day study plan!"
        rows = [left, right]
        pairs = find_near_duplicates(rows, threshold=0.8)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(normalized_text("Who created you?"), "who created you")

    def test_bengali_math_uses_bengali_digits_consistently(self) -> None:
        for record in build_records():
            if (
                record["metadata"]["category"] == "maths"
                and record["metadata"]["language"] == "Bengali"
            ):
                for message in record["messages"]:
                    self.assertFalse(
                        any("0" <= character <= "9" for character in message["content"]),
                        record["id"],
                    )


if __name__ == "__main__":
    unittest.main()
