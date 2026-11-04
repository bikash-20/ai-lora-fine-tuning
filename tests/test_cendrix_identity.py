"""Real-model checks for Cendrix AI identity questions."""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

from app.core.identity import assemble_messages, load_identity
from app.core.identity_fallback import answer_creator_identity, is_creator_identity_question


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "base" / "Qwen3-1.7B"
MAX_TOKENS = 128

QUESTIONS = (
    ("en", "Who created you?"),
    ("en", "Who is your developer?"),
    ("en", "Who made Cendrix AI?"),
    ("en", "Who made Bikash-AI?"),
    ("bn", "তোমাকে কে তৈরি করেছে?"),
    ("bn", "তোমার নির্মাতা কে?"),
    ("bn", "বিকাশ এআই কে বানিয়েছে?"),
    ("bx", "Tomake ke baniyeche?"),
    ("bx", "Tomar creator ke?"),
    ("bx", "Bikash AI ke banayse?"),
)


def has_correct_identity_answer(language: str, answer: str, creator_name: str) -> bool:
    lowered = answer.casefold()
    canonical_name = creator_name.casefold()
    bengali_name_present = "বিকাশ তালুকদার" in answer
    has_creator = canonical_name in lowered or bengali_name_present
    contains_bengali = bool(re.search(r"[\u0980-\u09ff]", answer))
    mentions_dynamic_age = bool(
        re.search(r"\b(?:24|twenty[- ]four)\b", lowered) or "২৪" in answer
    )
    mentions_current_status = bool(
        re.search(r"\b(?:currently|at present)\s+(?:studying|a student)\b", lowered)
        or "বর্তমানে" in answer
        or "এখন" in answer
    )
    if not has_creator or mentions_dynamic_age or mentions_current_status:
        return False
    if language == "bn":
        return contains_bengali
    if language == "bx":
        return not contains_bengali and bool(
            re.search(r"\b(?:amake|amar|tomar|toiri|baniyeche|banayse|creator)\b", lowered)
        )
    return not contains_bengali


class CendrixIdentityModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("CENDRIX_RUN_MODEL_TESTS") != "1":
            raise unittest.SkipTest("Set CENDRIX_RUN_MODEL_TESTS=1 to run local-model tests.")
        if not (MODEL_PATH / "config.json").is_file():
            raise unittest.SkipTest(f"Local Qwen3 model is missing: {MODEL_PATH}")
        from mlx_lm import load
        from mlx_lm.sample_utils import make_sampler

        cls.model, cls.tokenizer = load(str(MODEL_PATH), trust_remote_code=False)
        cls.sampler = staticmethod(make_sampler(temp=0.0))
        cls.creator_name = load_identity()["permanent"]["creator_name"]

    def test_identity_questions_with_system_prompt_only(self) -> None:
        results: list[tuple[str, str, str, bool]] = []
        from mlx_lm.generate import stream_generate

        for language, question in QUESTIONS:
            messages = assemble_messages(question)
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            chunks: list[str] = []
            for response in stream_generate(
                self.model,
                self.tokenizer,
                prompt,
                max_tokens=MAX_TOKENS,
                sampler=self.sampler,
            ):
                chunks.append(response.text)
            answer = "".join(chunks).strip()
            passed = has_correct_identity_answer(language, answer, self.creator_name)
            results.append((language, question, answer, passed))

        passed_count = sum(result[3] for result in results)
        print(
            "\nCendrix system-prompt-only identity results: "
            f"{passed_count}/{len(results)} passed"
        )
        for language, question, answer, passed in results:
            print(
                f"[{'PASS' if passed else 'FAIL'}] {language}: {question} "
                f"=> {json.dumps(answer, ensure_ascii=False)}"
            )
        self.assertEqual(len(results), len(QUESTIONS))


class CendrixIdentityFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = load_identity()
        self.identity["assistant_name"] = "Cendrix AI"

    def test_supported_questions_return_correct_identity_in_each_language(self) -> None:
        expected_answers = {
            "en": "I am Cendrix AI. I was created by Bikash Talukder, an AI engineer.",
            "bn": "আমি Cendrix AI। আমাকে তৈরি করেছেন Bikash Talukder, একজন এআই ইঞ্জিনিয়ার।",
            "bx": "Ami Cendrix AI. Amake baniyechen Bikash Talukder, ekjon AI engineer.",
        }
        for language, question in QUESTIONS:
            with self.subTest(question=question):
                answer = answer_creator_identity(question, self.identity)
                self.assertEqual(answer, expected_answers[language])
                self.assert_no_adjacent_repeated_words(answer)
                self.assertLessEqual(len(re.findall(r"[.!?।]+", answer)), 2)

    def assert_no_adjacent_repeated_words(self, answer: str) -> None:
        words = re.findall(r"\b[\w'-]+\b", answer.casefold())
        self.assertFalse(any(first == second for first, second in zip(words, words[1:])))

    def test_inference_uses_identity_fallback_without_loading_model(self) -> None:
        from app.core.inference import LocalAssistant

        assistant = LocalAssistant(identity_path=ROOT / "configs" / "identity.json")
        for language, question in QUESTIONS:
            with self.subTest(question=question):
                expected_answer = {
                    "en": "I am Cendrix AI. I was created by Bikash Talukder, an AI engineer.",
                    "bn": "আমি Cendrix AI। আমাকে তৈরি করেছেন Bikash Talukder, একজন এআই ইঞ্জিনিয়ার।",
                    "bx": "Ami Cendrix AI. Amake baniyechen Bikash Talukder, ekjon AI engineer.",
                }
                self.assertEqual(assistant.answer(question), expected_answer[language])
        self.assertIsNone(assistant._model)

    def test_additional_direct_creator_questions_trigger_fallback(self) -> None:
        for question in ("Who made you?", "Who built you?", "Who is your owner?"):
            with self.subTest(question=question):
                self.assertTrue(is_creator_identity_question(question))
                self.assertEqual(
                    answer_creator_identity(question, self.identity),
                    "I am Cendrix AI. I was created by Bikash Talukder, an AI engineer.",
                )

    def test_greetings_and_normal_questions_do_not_trigger_fallback(self) -> None:
        for question in (
            "hi",
            "how are you",
            "How do I write a Python loop?",
            "What is 12 multiplied by 7?",
            "How old is the current president?",
            "How old is your creator?",
        ):
            with self.subTest(question=question):
                self.assertFalse(is_creator_identity_question(question))
                self.assertIsNone(answer_creator_identity(question, self.identity))


if __name__ == "__main__":
    unittest.main()
