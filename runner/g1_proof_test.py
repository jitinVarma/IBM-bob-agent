"""
test_g1_ceiling.py — source of the G1 proof test.
This file is kept outside sample-repo and written into worktrees at runtime.
It is the hand-written proof test for Guarantee G1.
"""

G1_TEST_SOURCE = '''\
"""
G1 proof test: a single order request results in at most one gateway charge call.
Counts _do_charge() calls. base=PASS (no retry), head=FAIL (retry exists).
"""
import app.gateway as gw

def test_single_order_results_in_at_most_one_gateway_charge():
    has_retry = hasattr(gw, "_do_charge")

    if not has_retry:
        attempts = 1
    else:
        original = gw._do_charge
        attempts_list = []
        fail_first = {"done": False}

        def counting_do_charge(amount, idempotency_key):
            attempts_list.append(1)
            if not fail_first["done"]:
                fail_first["done"] = True
                raise gw.GatewayError("transient")
            return original(amount, idempotency_key)

        gw._do_charge = counting_do_charge
        try:
            gw.charge(1.0, "g1-proof-key")
        except gw.GatewayError:
            pass
        finally:
            gw._do_charge = original

        attempts = len(attempts_list)

    assert attempts <= 1, (
        f"G1 VIOLATED: {attempts} gateway charge attempts for one logical request "
        f"(ceiling=1). A single order request must result in at most one "
        f"gateway charge call (docs/ADR-001.md:14)."
    )
'''
