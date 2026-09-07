"""Workflow loading and graph helpers.

The bundled JSONs are API-format graphs (what ``/prompt`` accepts), stored
under ``h3turing/data/``. They are field-tested configurations - resist the
urge to "clean them up"; every explicit parameter exists because v3-API nodes
do not apply server-side defaults over /prompt (missing one = HTTP 400).
"""

from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any

PROMPT_PLACEHOLDER = "__H3_PROMPT__"


def load(name: str) -> dict[str, Any]:
    """Load a bundled workflow as a deep-copyable API graph.

    ``name`` is a data file name (with or without .json), e.g.
    ``"h3_w4a8_t2v_compat_api"``.
    """
    if not name.endswith(".json"):
        name += ".json"
    text = resources.files("h3turing").joinpath("data", name).read_text(encoding="utf-8")
    return json.loads(text)


def set_prompt(graph: dict[str, Any], text: str) -> dict[str, Any]:
    """Replace the ``__H3_PROMPT__`` placeholder (in place). Returns the graph."""
    hits = 0
    for node in graph.values():
        inputs = node.get("inputs") if isinstance(node, dict) else None
        if inputs and inputs.get("prompt") == PROMPT_PLACEHOLDER:
            inputs["prompt"] = text
            hits += 1
    if hits == 0:
        raise ValueError(
            f"no {PROMPT_PLACEHOLDER!r} placeholder found - this workflow may already "
            "have a prompt baked in; set node prompt directly instead"
        )
    return graph


def set_seed(graph: dict[str, Any], seed: int) -> dict[str, Any]:
    """Set the noise seed (in place). Returns the graph."""
    for node in graph.values():
        inputs = node.get("inputs") if isinstance(node, dict) else None
        if inputs and "noise_seed" in inputs:
            inputs["noise_seed"] = int(seed)
    return graph


def render(graph: dict[str, Any]) -> dict[str, Any]:
    """Deep copy ready for JSON serialization to /prompt."""
    return copy.deepcopy(graph)
