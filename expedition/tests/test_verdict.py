import unittest

from expedition.evidence import EvidenceAtom, geometry_hash, utc_now
from expedition.plan import compile_plan
from expedition.verdict import judge


def atom(
    field,
    value,
    *,
    kind="FACT",
    effect="VETO",
    status="replay",
    candidate="x",
    support=None,
):
    now = utc_now()
    return EvidenceAtom(
        atom_id=f"{candidate}:{field}",
        candidate_id=candidate,
        question_id="t",
        field_id=field,
        kind=kind,
        status=status,
        decision_effect=effect,
        value=value,
        unit=None,
        source="test",
        source_url=None,
        source_family="TEST",
        independence_group="TEST",
        authority="authoritative",
        support=support or {"kind": "point", "lat": 0, "lng": 0, "geometry_hash": geometry_hash(0, 0)},
        observed_at=None,
        fetched_at=now,
        dataset_vintage=None,
        ttl=None,
        confidence="high",
        notes=None,
        failure=None,
        cost={"credits": 0, "tokens": 0, "unit": "x"},
        citation={"source": "test", "source_url": None, "fetched_at": now, "dataset_vintage": None},
        transform_version="t",
        cache_identity="t",
        live_label="replay" if status != "live" else "live",
    )


class VerdictTests(unittest.TestCase):
    def test_sfha_rejects_warehouse(self):
        plan = compile_plan("warehouse")
        out = judge(plan, "san_leon", [
            atom("fema_flood_zone", "AE"),
            atom("within_floodplain_polygon", True, effect="VETO"),
        ])
        self.assertEqual(out["verdict"], "reject")
        self.assertIn("mapped_sfha", out["reasons"])

    def test_uncultivated_rejects_farm(self):
        plan = compile_plan("farm")
        out = judge(plan, "manhattan", [atom("is_cultivated", False, effect="VETO")])
        self.assertEqual(out["verdict"], "reject")
        self.assertIn("not_cultivated", out["reasons"])

    def test_ny_farm_not_rejected_for_state(self):
        plan = compile_plan("farm")
        out = judge(plan, "elba_ny", [
            atom("is_cultivated", True, effect="VETO"),
            atom("fema_flood_zone", "X", effect="GATE"),
        ])
        self.assertNotEqual(out["verdict"], "reject")
        self.assertNotIn("state_is_new_york", out["reasons"])

    def test_failed_gate_is_conditional_not_fit(self):
        plan = compile_plan("warehouse", flood_intolerant=True)
        out = judge(plan, "x", [
            atom("fema_flood_zone", None, kind="FAILED", effect="GATE", status="failed"),
        ])
        self.assertEqual(out["verdict"], "conditional")

    def test_site_form_mismatch_is_a_deterministic_reject(self):
        plan = compile_plan("farm", site_form="existing_asset")
        out = judge(
            plan,
            "farm",
            [atom("is_cultivated", True)],
            candidate={"site_form": "developable_land"},
        )
        self.assertEqual("reject", out["verdict"])
        self.assertIn("site_form_mismatch", out["reasons"])

    def test_declared_size_and_budget_are_blocking_until_verified(self):
        plan = compile_plan(
            "warehouse",
            size_band="100k_250k_sqft",
            budget_band="10m_25m",
        )
        out = judge(
            plan,
            "candidate",
            [atom("fema_flood_zone", "X")],
            candidate={"site_form": "either"},
        )
        gaps = {gap["question_id"] for gap in out["gaps"]}
        self.assertIn("site_size", gaps)
        self.assertIn("acquisition_budget", gaps)
        self.assertEqual("conditional", out["verdict"])

    def test_route_hard_maximum_rejects_a_slow_fact(self):
        plan = compile_plan(
            "warehouse",
            route_anchors=[{
                "id": "customer",
                "name": "Customer",
                "lat": 30,
                "lng": -96,
                "max_minutes": 60,
            }],
        )
        out = judge(
            plan,
            "candidate",
            [
                atom("fema_flood_zone", "X"),
                atom(
                    "route_duration_s",
                    3660,
                    effect="INFORM",
                    support={"kind": "network", "destination_id": "customer"},
                ),
            ],
            candidate={"site_form": "either"},
        )
        self.assertEqual("reject", out["verdict"])
        self.assertIn("route_time_exceeds_max:customer", out["reasons"])

    def test_engine_does_not_import_gates(self):
        import expedition.engine as engine
        with open(engine.__file__, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("gates.json", text)
        self.assertNotIn("verify.score", text)
        self.assertNotIn("expected_gate", text)
