import json
import tempfile
import unittest
from pathlib import Path

from app.core.identity import assemble_messages, load_identity


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "configs" / "identity.json"


class IdentityPromptTests(unittest.TestCase):
    def test_runtime_prompt_injects_identity_for_all_supported_languages(self) -> None:
        questions = (
            "Who created you and how old is he?",
            "তোমার নির্মাতার বয়স কত?",
            "Tomar creator-er boyosh koto?",
        )
        for question in questions:
            with self.subTest(question=question):
                messages = assemble_messages(question)
                self.assertEqual(messages[1]["content"], question)
                self.assertIn("You are Cendrix AI", messages[0]["content"])
                self.assertIn("Bikash Talukder", messages[0]["content"])
                self.assertIn("Permanent creator identity:", messages[0]["content"])
                self.assertIn("24 (as of 2026-11-04)", messages[0]["content"])
                self.assertIn("Studying Computer Science and Engineering", messages[0]["content"])

    def test_identity_update_changes_runtime_prompt_without_model_changes(self) -> None:
        identity = load_identity(IDENTITY_PATH)
        with tempfile.TemporaryDirectory() as temp_dir:
            changed_path = Path(temp_dir) / "identity.json"
            identity["dynamic_creator"]["age_years"] = 25
            identity["dynamic_creator"]["age_as_of"] = "2027-01-01"
            identity["dynamic_creator"]["current_status"] = "Working as an AI engineer"
            identity["dynamic_creator"]["status_as_of"] = "2027-01-01"
            changed_path.write_text(json.dumps(identity), encoding="utf-8")

            old_prompt = assemble_messages("Who is your creator?")[0]["content"]
            updated_prompt = assemble_messages(
                "Who is your creator?", identity_path=changed_path
            )[0]["content"]

        self.assertIn("24 (as of 2026-11-04)", old_prompt)
        self.assertIn("25 (as of 2027-01-01)", updated_prompt)
        self.assertIn("Working as an AI engineer", updated_prompt)
        self.assertIn("You were created by Bikash Talukder", updated_prompt)
        self.assertNotEqual(old_prompt, updated_prompt)

    def test_training_prompt_does_not_embed_real_creator_identity(self) -> None:
        from app.core.identity import render_training_prompt

        prompt = render_training_prompt()
        self.assertIn("You are Bikash-AI", prompt)
        self.assertNotIn("Bikash Talukder", prompt)
        self.assertIn("No creator-specific facts are supplied.", prompt)


if __name__ == "__main__":
    unittest.main()
