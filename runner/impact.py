"""
impact.py — parse output from the three impact subagents.

The three agents (callers, contract, intent) run concurrently as Bob subagents.
Each returns structured text (≤800 tokens). This module parses their output
into intermediate dicts that candidates.py uses for ranking.
"""
from __future__ import annotations
import json
import re


def parse_callers(text: str) -> dict:
    """
    Parse callers-agent output.
    Expected fields:
        call_sites: list of {symbol, file, line, guarded: bool}
        unguarded_count: int
    """
    return _extract_json_block(text, default={"call_sites": [], "unguarded_count": 0})


def parse_contract(text: str) -> dict:
    """
    Parse contract-agent output.
    Expected fields:
        nullability: list of {symbol, nullable: bool}
        ordering_deps: list of str
        idempotent: bool | None
        exceptions_raised: list of str
        return_shape: str | None
        side_effects: list of str
    """
    return _extract_json_block(text, default={
        "nullability": [],
        "ordering_deps": [],
        "idempotent": None,
        "exceptions_raised": [],
        "return_shape": None,
        "side_effects": [],
    })


def parse_intent(text: str) -> dict:
    """
    Parse intent-agent output.
    Expected fields:
        touched_guarantees: list of guarantee ids
        pattern: bypass | weaken | multiply | none
        cross_team_defeat: {guarantee_id, branch_a, branch_b} | None
        blast_radius: int  (number of call sites affected)
    """
    return _extract_json_block(text, default={
        "touched_guarantees": [],
        "pattern": "none",
        "cross_team_defeat": None,
        "blast_radius": 0,
    })


def _extract_json_block(text: str, default: dict) -> dict:
    """Extract the first JSON object or array from agent output text."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        raw = match.group(1)
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return default
        raw = match.group(0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default
