"""Local MLX inference with a deterministic identity-answer boundary."""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.core.identity import DEFAULT_IDENTITY_PATH, DEFAULT_PROMPT_PATH, load_identity, render_system_prompt
from app.core.identity_fallback import answer_creator_identity


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = ROOT / "models" / "base" / "Qwen3-1.7B"
MAX_TOKENS = 512
MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_CHARS = 16_000
logger = logging.getLogger(__name__)


class FriendlyInferenceError(RuntimeError):
    """An inference failure suitable for showing to the local user."""


class LocalAssistant:
    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
        identity_path: Path = DEFAULT_IDENTITY_PATH,
        prompt_path: Path = DEFAULT_PROMPT_PATH,
        max_tokens: int = MAX_TOKENS,
    ) -> None:
        self.model_path = model_path
        self.identity_path = identity_path
        self.prompt_path = prompt_path
        self.max_tokens = max_tokens
        self._model: Any = None
        self._tokenizer: Any = None
        self._sampler: Any = None

    def answer(
        self, question: str, history: list[dict[str, str]] | None = None
    ) -> str:
        if not question.strip():
            raise ValueError("Please enter a message.")
        identity = load_identity(self.identity_path)
        fixed_answer = answer_creator_identity(question, identity)
        if fixed_answer is not None:
            return fixed_answer

        self._ensure_model()
        messages = [{"role": "system", "content": render_system_prompt(identity, self.prompt_path)}]
        retained: list[dict[str, str]] = []
        remaining_chars = MAX_HISTORY_CHARS
        for item in reversed((history or [])[-MAX_HISTORY_MESSAGES:]):
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                bounded_content = content[-remaining_chars:]
                if bounded_content.strip():
                    retained.append({"role": role, "content": bounded_content})
                    remaining_chars -= len(bounded_content)
                if remaining_chars <= 0:
                    break
        messages.extend(reversed(retained))
        messages.append({"role": "user", "content": question[:8000]})

        try:
            prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            from mlx_lm.generate import stream_generate

            parts: list[str] = []
            for response in stream_generate(
                self._model,
                self._tokenizer,
                prompt,
                max_tokens=self.max_tokens,
                sampler=self._sampler,
            ):
                parts.append(response.text)
            answer = "".join(parts).strip()
            if not answer:
                raise FriendlyInferenceError(
                    "Cendrix could not create an answer. Please try asking in a different way."
                )
            return answer
        except FriendlyInferenceError:
            raise
        except MemoryError as error:
            raise FriendlyInferenceError(
                "Cendrix ran out of memory. Close other apps and try a shorter message."
            ) from error
        except Exception as error:
            if "memory" in str(error).casefold() or "alloc" in str(error).casefold():
                raise FriendlyInferenceError(
                    "Cendrix ran out of memory. Close other apps and try a shorter message."
                ) from error
            logger.exception("Local generation failed")
            raise FriendlyInferenceError(
                "Cendrix could not finish that response. Please try again."
            ) from error

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        if not (self.model_path / "config.json").is_file():
            raise FriendlyInferenceError(
                "The local Qwen3 model was not found. Check that the model files are in "
                "models/base/Qwen3-1.7B."
            )
        try:
            import mlx.core as mx
            from mlx_lm import load
            from mlx_lm.sample_utils import make_sampler

            self._model, self._tokenizer = load(
                str(self.model_path), trust_remote_code=False
            )
            self._sampler = make_sampler(temp=0.0)
            mx.eval(self._model.parameters())
        except MemoryError as error:
            self._model = self._tokenizer = self._sampler = None
            raise FriendlyInferenceError(
                "Cendrix could not load the model because memory is low. Close other apps and retry."
            ) from error
        except Exception as error:
            self._model = self._tokenizer = self._sampler = None
            if "memory" in str(error).casefold() or "alloc" in str(error).casefold():
                raise FriendlyInferenceError(
                    "Cendrix could not load the model because memory is low. Close other apps and retry."
                ) from error
            logger.exception("Loading the local MLX model failed")
            raise FriendlyInferenceError(
                "Cendrix could not load the local model. Check the model files and runtime setup."
            ) from error
