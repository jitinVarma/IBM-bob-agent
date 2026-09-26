"""
CLI entry point for Witness.

Usage:
    witness gate     --repo <path> --base main --head <ref> [--with <ref>...]
    witness standing --repo <path> --ref HEAD
    witness bench    --repo <path>
    witness replay   --run <run-id>
"""
from __future__ import annotations
import argparse
import sys


def cmd_gate(args: argparse.Namespace) -> int:
    """Pre-merge gate: does merging head defeat a guarantee main or another team already holds?"""
    print(f"[gate] repo={args.repo} base={args.base} head={args.head} with={args.with_branches}")
    print("[gate] Not yet implemented — M3 onwards")
    return 0


def cmd_standing(args: argparse.Namespace) -> int:
    """Standing auditor: does this code contradict its own documented intent?"""
    print(f"[standing] repo={args.repo} ref={args.ref}")
    print("[standing] Not yet implemented — M4 onwards")
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    """Benchmark harness: run all synthetic cases and write bench/RESULTS.md."""
    print(f"[bench] repo={args.repo}")
    print("[bench] Not yet implemented — M8")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Replay a stored run in the dashboard with no agent calls."""
    print(f"[replay] run={args.run}")
    print("[replay] Not yet implemented — M7")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="witness",
        description="Witness — pre-merge gate and standing code auditor",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # gate
    p_gate = sub.add_parser("gate", help="Pre-merge gate: prove a guarantee is defeated by a merge")
    p_gate.add_argument("--repo", required=True, help="Path to the git repository")
    p_gate.add_argument("--base", required=True, help="Base branch (e.g. main)")
    p_gate.add_argument("--head", required=True, help="Head branch or SHA to gate")
    p_gate.add_argument("--with", dest="with_branches", nargs="*", default=[],
                        help="Other open branches touching the same surface")
    p_gate.set_defaults(func=cmd_gate)

    # standing
    p_standing = sub.add_parser("standing", help="Standing auditor: find self-contradictions in current code")
    p_standing.add_argument("--repo", required=True, help="Path to the git repository")
    p_standing.add_argument("--ref", default="HEAD", help="Git ref to audit (default: HEAD)")
    p_standing.set_defaults(func=cmd_standing)

    # bench
    p_bench = sub.add_parser("bench", help="Benchmark: run all synthetic cases unattended")
    p_bench.add_argument("--repo", required=True, help="Path to the git repository")
    p_bench.set_defaults(func=cmd_bench)

    # replay
    p_replay = sub.add_parser("replay", help="Replay a stored run in the dashboard (no agent calls)")
    p_replay.add_argument("--run", required=True, help="Run ID (matches dashboard/data/run-<id>.json)")
    p_replay.set_defaults(func=cmd_replay)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
