"""
test_m3_harness.py — M3 acceptance test for the differential execution harness.

Runs two tests through the harness:
1. Calibration (isolation self-check): a test that asserts a constant that differs
   between base and head. Must return base=PASS, head=FAIL. If both return the
   same result, print "HARNESS ISOLATION FAILURE" and raise.

2. G1 proof test: must return base=PASS (team-a pre-merge), head=FAIL (merge).

Run from the project root:
    python -m pytest runner/test_m3_harness.py -v
"""
import sys
import pytest
from pathlib import Path
from runner.g1_proof_test import G1_TEST_SOURCE

REPO = Path(__file__).parent.parent / "sample-repo"
BASE_REF = "a4477c4"   # team-a/rate-limit before merge — no _do_charge
HEAD_REF = "db61b21"   # merge commit — has _do_charge + retry

# Calibration test: asserts _do_charge does NOT exist.
# PASS on base (no _do_charge), FAIL on head (has _do_charge).
CALIBRATION_TEST = """\
import app.gateway as gw

def test_harness_calibration():
    # This test PASSES when _do_charge does not exist (base/team-a only)
    # and FAILS when _do_charge exists (head/merged).
    assert not hasattr(gw, "_do_charge"), (
        "Calibration FAIL: _do_charge exists on this ref — "
        "this is the merged branch, not the base."
    )
"""


def test_harness_isolation_calibration():
    """
    Harness self-check: calibration test must return base=PASS, head=FAIL.
    If both sides return the same result, HARNESS ISOLATION FAILURE.
    """
    from runner.worktrees import create, teardown
    from runner.execute import run_test

    base_wt = create(REPO, BASE_REF, "m3-calib-base")
    head_wt = create(REPO, HEAD_REF, "m3-calib-head")

    try:
        base_res = run_test(base_wt, CALIBRATION_TEST, "test_m3_calibration.py")
        head_res = run_test(head_wt, CALIBRATION_TEST, "test_m3_calibration.py")
    finally:
        teardown(base_wt)
        teardown(head_wt)

    base_result = base_res["result"]
    head_result = head_res["result"]

    if base_result == head_result:
        print(
            f"\nHARNESS ISOLATION FAILURE: both sides returned '{base_result}'.\n"
            "The worktrees are not isolated — both are importing from the same installed package.\n"
            "Check: (1) no pip install -e . was run, (2) PYTHONPATH is cleared, "
            "(3) cwd is set to the worktree.",
            file=sys.stderr,
        )
        pytest.fail(
            f"HARNESS ISOLATION FAILURE: base={base_result} head={head_result} (must differ)"
        )

    assert base_result == "PASS", f"Calibration: base should PASS, got {base_result}\n{base_res['stderr_excerpt']}"
    assert head_result == "FAIL", f"Calibration: head should FAIL, got {head_result}\n{head_res['stderr_excerpt']}"


def test_g1_proof_differential():
    """
    G1 proof: base=PASS (team-a, no retry), head=FAIL (merge, retries exist).
    """
    from runner.worktrees import create, teardown
    from runner.execute import run_test

    base_wt = create(REPO, BASE_REF, "m3-g1-base")
    head_wt = create(REPO, HEAD_REF, "m3-g1-head")

    try:
        base_res = run_test(base_wt, G1_TEST_SOURCE, "test_g1_ceiling.py")
        head_res = run_test(head_wt, G1_TEST_SOURCE, "test_g1_ceiling.py")
    finally:
        teardown(base_wt)
        teardown(head_wt)

    base_result = base_res["result"]
    head_result = head_res["result"]

    assert base_result == "PASS", (
        f"G1 proof: base ({BASE_REF}) should PASS, got {base_result}\n"
        f"stderr: {base_res['stderr_excerpt']}"
    )
    assert head_result == "FAIL", (
        f"G1 proof: head ({HEAD_REF}) should FAIL, got {head_result}\n"
        f"stderr: {head_res['stderr_excerpt']}"
    )
