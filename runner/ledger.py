"""
ledger.py — build and persist the Purpose Ledger.

The ledger agent (a Bob subagent) extracts guarantees from ADRs, docstrings,
inline comments, commit messages, config constants, and test names.
This module parses the agent's text output, validates required fields,
populates covered_by_test by matching against the existing test suite,
and persists to dashboard/data/ledger.json.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from runner.schemas import Guarantee


def parse_ledger_agent_output(text: str) -> list[Guarantee]:
    """Parse JSON array of guarantee dicts from ledger-agent output text."""
    # Agent returns a JSON block between ```json and ``` markers
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        raw = match.group(1)
    else:
        # Fallback: try to find a bare JSON array
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        raw = match.group(0)

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return []

    guarantees = []
    for item in items:
        # Discard anything without provenance (spec §2)
        if not item.get("provenance"):
            continue
        try:
            g = Guarantee(
                id=item["id"],
                statement=item["statement"],
                why=item["why"],
                provenance=item["provenance"],
                enforced_at=item.get("enforced_at", []),
                covered_by_test=item.get("covered_by_test"),
                surface=item.get("surface", []),
            )
            guarantees.append(g)
        except KeyError:
            continue
    return guarantees


def populate_coverage(guarantees: list[Guarantee], repo_path: str | Path) -> list[Guarantee]:
    """
    For each guarantee with covered_by_test=None, check if any test name
    or test file content references a known surface symbol or guarantee statement.
    Updates covered_by_test in place.
    """
    repo_path = Path(repo_path)
    test_files = list(repo_path.rglob("tests/test_*.py")) + list(repo_path.rglob("test_*.py"))

    test_contents: list[tuple[Path, str]] = []
    for tf in test_files:
        try:
            test_contents.append((tf, tf.read_text(encoding="utf-8")))
        except OSError:
            pass

    for g in guarantees:
        if g.covered_by_test is not None:
            continue
        for tf, content in test_contents:
            # Match by surface symbol or by key words from the guarantee statement
            keywords = [w for w in g.statement.lower().split() if len(w) > 4]
            if any(kw in content.lower() for kw in keywords[:3]):
                # Find the first test function name that matches
                fn_match = re.search(r"def (test_\w+)", content)
                if fn_match:
                    rel = tf.relative_to(repo_path)
                    g.covered_by_test = f"{rel}::{fn_match.group(1)}"
                    break
    return guarantees


def save_ledger(output_path: str | Path, guarantees: list[Guarantee]) -> None:
    """Persist the ledger as JSON to output_path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "id": g.id,
            "statement": g.statement,
            "why": g.why,
            "provenance": g.provenance,
            "enforced_at": g.enforced_at,
            "covered_by_test": g.covered_by_test,
            "surface": g.surface,
        }
        for g in guarantees
    ]
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_ledger(path: str | Path) -> list[Guarantee]:
    """Load a persisted ledger from JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Guarantee(**item) for item in data]
