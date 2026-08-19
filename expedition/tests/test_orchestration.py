import threading
import unittest

from expedition.orchestration import (
    ActivationDecision,
    DependencyMode,
    OutcomeKind,
    RetryableWorkstreamError,
    Workstream,
    WorkstreamOutcome,
    WorkstreamStatus,
    run_workstreams,
)


class OrchestrationTests(unittest.TestCase):
    def test_independent_workstreams_run_in_parallel_but_return_in_declared_order(self):
        second_started = threading.Event()

        def first(_context):
            if not second_started.wait(1):
                raise AssertionError("independent Workstreams did not overlap")
            return "first"

        def second(_context):
            second_started.set()
            return "second"

        result = run_workstreams(
            [
                Workstream("hazards", "Is the site hazard-safe?", first),
                Workstream("access", "Can trucks reach the site?", second),
            ],
            max_workers=2,
        )

        self.assertEqual(
            [row.workstream_id for row in result.workstreams],
            ["hazards", "access"],
        )
        self.assertEqual(
            [row.outcome.payload for row in result.workstreams],
            ["first", "second"],
        )
        self.assertTrue(
            all(row.status is WorkstreamStatus.SUCCEEDED for row in result.workstreams)
        )

    def test_dependency_payload_is_available_after_predecessor_commits(self):
        def deepen(context):
            screen = context.snapshot.outcome("screen")
            return {"screened": screen.payload["screened"]}

        result = run_workstreams(
            [
                Workstream(
                    "screen",
                    "Does the candidate pass the cheap screen?",
                    lambda _context: {"screened": True},
                ),
                Workstream(
                    "deepen",
                    "Can temporal evidence change the decision?",
                    deepen,
                    depends_on=("screen",),
                ),
            ]
        )

        self.assertEqual(result.record("deepen").outcome.payload, {"screened": True})
        running = [
            row.workstream_id
            for row in result.transitions
            if row.to_status is WorkstreamStatus.RUNNING
        ]
        self.assertEqual(running, ["screen", "deepen"])

    def test_retry_state_is_typed_bounded_and_preserves_partial_payload(self):
        attempts = []

        def flaky(context):
            attempts.append(context.attempt)
            if context.attempt == 1:
                raise RetryableWorkstreamError(
                    "provider timeout", payload={"atoms": ["partial"]}
                )
            return WorkstreamOutcome.success({"atoms": ["complete"]})

        result = run_workstreams(
            [
                Workstream(
                    "history",
                    "Has land behavior changed?",
                    flaky,
                    max_attempts=2,
                )
            ]
        )
        record = result.record("history")

        self.assertEqual(attempts, [1, 2])
        self.assertEqual(
            [attempt.outcome.kind for attempt in record.attempts],
            [OutcomeKind.RETRY, OutcomeKind.SUCCESS],
        )
        self.assertEqual(record.attempts[0].outcome.payload, {"atoms": ["partial"]})
        self.assertIn(
            WorkstreamStatus.RETRY_PENDING,
            [row.to_status for row in result.transitions],
        )
        self.assertEqual(record.status, WorkstreamStatus.SUCCEEDED)

    def test_retry_limit_becomes_failure(self):
        result = run_workstreams(
            [
                Workstream(
                    "source",
                    "Can the official source answer?",
                    lambda _context: WorkstreamOutcome.retry("timeout"),
                    max_attempts=2,
                )
            ]
        )

        record = result.record("source")
        self.assertEqual(record.status, WorkstreamStatus.FAILED)
        self.assertEqual(len(record.attempts), 2)
        self.assertEqual(record.reason, "retry limit reached: timeout")

    def test_reliable_veto_cancels_downstream_but_allows_exempt_witness(self):
        calls = []

        def screen(_context):
            calls.append("screen")
            return WorkstreamOutcome.success(
                {"zone": "AE"}, reliable_veto=True
            )

        def should_not_run(_context):
            calls.append("route")

        def witness(_context):
            calls.append("witness")
            return "rewind retained"

        result = run_workstreams(
            [
                Workstream("screen", "Is there a reliable hard veto?", screen),
                Workstream(
                    "route",
                    "Can the route serve the operation?",
                    should_not_run,
                    depends_on=("screen",),
                ),
                Workstream(
                    "witness",
                    "What explains the veto?",
                    witness,
                    depends_on=("screen",),
                    cancel_on_veto=False,
                ),
            ]
        )

        self.assertEqual(calls, ["screen", "witness"])
        self.assertEqual(result.reliable_vetoes, ("screen",))
        self.assertEqual(result.record("route").status, WorkstreamStatus.CANCELLED)
        self.assertEqual(result.record("witness").status, WorkstreamStatus.SUCCEEDED)

    def test_adaptive_activation_selects_only_material_deepening(self):
        def material(snapshot):
            payload = snapshot.outcome("screen").payload
            if payload["flood_disagreement"]:
                return ActivationDecision.run("disagreement needs temporal witness")
            return ActivationDecision.skip("present-state fact is sufficient")

        result = run_workstreams(
            [
                Workstream(
                    "screen",
                    "What does the present-state screen show?",
                    lambda _context: {"flood_disagreement": True},
                ),
                Workstream(
                    "flood-rewind",
                    "Has flood behavior changed?",
                    lambda _context: "witness",
                    depends_on=("screen",),
                    activate_when=material,
                ),
                Workstream(
                    "unneeded-source-scout",
                    "Is another source material?",
                    lambda _context: "must not run",
                    depends_on=("screen",),
                    activate_when=lambda _snapshot: ActivationDecision.skip(
                        "no unresolved contradiction"
                    ),
                ),
            ]
        )

        self.assertEqual(
            result.record("flood-rewind").status, WorkstreamStatus.SUCCEEDED
        )
        skipped = result.record("unneeded-source-scout")
        self.assertEqual(skipped.status, WorkstreamStatus.SKIPPED)
        self.assertEqual(skipped.reason, "no unresolved contradiction")

    def test_budget_exhaustion_stops_retry_and_blocks_dependent(self):
        result = run_workstreams(
            [
                Workstream(
                    "metered",
                    "Can the metered source answer?",
                    lambda _context: WorkstreamOutcome.retry("quota"),
                    max_attempts=3,
                    cost_per_attempt=2,
                ),
                Workstream(
                    "cheap-independent",
                    "Can the fixture answer another question?",
                    lambda _context: "yes",
                    cost_per_attempt=1,
                ),
                Workstream(
                    "dependent",
                    "Can the metered result be reconciled?",
                    lambda _context: "must not run",
                    depends_on=("metered",),
                ),
            ],
            max_workers=2,
            budget_limit=3,
        )

        self.assertEqual(result.budget_spent, 3)
        self.assertEqual(result.budget_remaining, 0)
        self.assertTrue(result.budget_exhausted)
        self.assertEqual(
            result.record("metered").status, WorkstreamStatus.BUDGET_EXHAUSTED
        )
        self.assertEqual(
            result.record("cheap-independent").status, WorkstreamStatus.SUCCEEDED
        )
        self.assertEqual(result.record("dependent").status, WorkstreamStatus.BLOCKED)

    def test_terminal_dependency_mode_can_drive_a_failure_fallback(self):
        result = run_workstreams(
            [
                Workstream(
                    "aerial",
                    "Is Aerial View available?",
                    lambda _context: WorkstreamOutcome.failure("typed 404"),
                ),
                Workstream(
                    "maps-3d",
                    "What present-day visual fallback is available?",
                    lambda context: context.snapshot.outcome("aerial").reason,
                    depends_on=("aerial",),
                    dependency_mode=DependencyMode.TERMINAL,
                    activate_when=lambda snapshot: (
                        snapshot.outcome("aerial").kind is OutcomeKind.FAILURE
                    ),
                ),
            ]
        )

        self.assertEqual(result.record("aerial").status, WorkstreamStatus.FAILED)
        self.assertEqual(result.record("maps-3d").status, WorkstreamStatus.SUCCEEDED)
        self.assertEqual(result.record("maps-3d").outcome.payload, "typed 404")

    def test_on_transition_fires_after_each_committed_state_change(self):
        seen = []

        def first(_context):
            return "one"

        def second(_context):
            return "two"

        result = run_workstreams(
            [
                Workstream("screen", "Cheap screen?", first),
                Workstream(
                    "rewind",
                    "Has flood behavior changed?",
                    second,
                    depends_on=("screen",),
                ),
            ],
            on_transition=lambda transition, _snapshot: seen.append(
                (transition.workstream_id, transition.to_status.value)
            ),
        )
        self.assertEqual(
            [row.status for row in result.workstreams],
            [WorkstreamStatus.SUCCEEDED, WorkstreamStatus.SUCCEEDED],
        )
        self.assertGreaterEqual(len(seen), 4)
        self.assertEqual(seen[0], ("screen", "ready"))
        self.assertIn(("screen", "running"), seen)
        self.assertIn(("screen", "succeeded"), seen)
        screen_succeeded = seen.index(("screen", "succeeded"))
        rewind_running = seen.index(("rewind", "running"))
        self.assertLess(screen_succeeded, rewind_running)

    def test_graph_validation_rejects_unknown_dependencies_and_cycles(self):
        with self.assertRaisesRegex(ValueError, "unknown dependency"):
            run_workstreams(
                [
                    Workstream(
                        "x", "Question x", lambda _context: None, depends_on=("y",)
                    )
                ]
            )
        with self.assertRaisesRegex(ValueError, "cycle"):
            run_workstreams(
                [
                    Workstream(
                        "x", "Question x", lambda _context: None, depends_on=("y",)
                    ),
                    Workstream(
                        "y", "Question y", lambda _context: None, depends_on=("x",)
                    ),
                ]
            )


if __name__ == "__main__":
    unittest.main()
