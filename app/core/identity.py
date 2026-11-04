"""Versioned identity loading and system-prompt assembly."""

from __future__ import annotations

import json
from pathlib import Path
from string import Template
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IDENTITY_PATH = ROOT / "configs" / "identity.json"
DEFAULT_PROMPT_PATH = ROOT / "app" / "prompts" / "system_prompt.txt"


def load_identity(path: Path = DEFAULT_IDENTITY_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as identity_file:
        identity = json.load(identity_file)
    required = ("identity_version", "assistant_name", "permanent", "dynamic_creator")
    if any(key not in identity for key in required):
        raise ValueError(f"Identity configuration is missing required fields: {path}")
    permanent = identity["permanent"]
    dynamic = identity["dynamic_creator"]
    if any(key not in permanent for key in ("creator_name", "creator_role", "project_origin")):
        raise ValueError(f"Identity configuration has incomplete permanent facts: {path}")
    if any(key not in dynamic for key in ("age_years", "age_as_of", "current_status", "status_as_of")):
        raise ValueError(f"Identity configuration has incomplete dynamic facts: {path}")
    if not isinstance(dynamic["age_years"], int) or dynamic["age_years"] < 0:
        raise ValueError(f"Identity configuration has an invalid creator age: {path}")
    return identity


def _permanent_creator_identity(identity: dict[str, Any]) -> str:
    permanent = identity["permanent"]
    return (
        f"\nPermanent creator identity: You were created by {permanent['creator_name']}, "
        f"a {permanent['creator_role']}. {permanent['project_origin']}"
    )


def _dynamic_creator_facts(identity: dict[str, Any]) -> str:
    dynamic = identity["dynamic_creator"]
    return (
        f"Creator age: {dynamic['age_years']} (as of {dynamic['age_as_of']})\n"
        f"Creator current status: {dynamic['current_status']} "
        f"(as of {dynamic['status_as_of']})"
    )


def render_system_prompt(
    identity: dict[str, Any], template_path: Path = DEFAULT_PROMPT_PATH
) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(
        assistant_name=identity["assistant_name"],
        permanent_creator_identity=_permanent_creator_identity(identity),
        current_creator_facts=_dynamic_creator_facts(identity),
    )


def assemble_messages(
    user_message: str,
    identity_path: Path = DEFAULT_IDENTITY_PATH,
    template_path: Path = DEFAULT_PROMPT_PATH,
) -> list[dict[str, str]]:
    if not user_message.strip():
        raise ValueError("User message must not be empty")
    identity = load_identity(identity_path)
    return [
        {"role": "system", "content": render_system_prompt(identity, template_path)},
        {"role": "user", "content": user_message},
    ]


def render_training_prompt(identity_facts: str = "No creator-specific facts are supplied.") -> str:
    template = Template(DEFAULT_PROMPT_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        assistant_name="Bikash-AI",
        permanent_creator_identity="",
        current_creator_facts=identity_facts,
    )
