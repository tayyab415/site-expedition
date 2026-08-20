"""Deterministic, bounded orchestration for question-owned Workstreams.

The module deliberately has one execution seam: :func:`run_workstreams`.  A
caller declares a DAG of question-owned :class:`Workstream` objects and gets a
complete, ordered trace back.  Provider calls remain outside this module and
are supplied as Workstream functions, which keeps orchestration reproducible
without coupling it to any particular adapter.

Ready work is executed in bounded *waves*.  Members of a wave run concurrently,
but their outcomes and transitions are committed in declaration order.  A
reliable veto therefore cancels later, unstarted work deterministically; work
already admitted to the same wave is allowed to finish and its evidence is
preserved.
"""

from __future__ import annotations

import math
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


class WorkstreamStatus(str, Enum):
    """Typed states in the Workstream state machine."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    RETRY_PENDING = "retry_pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    BUDGET_EXHAUSTED = "budget_exhausted"
    BLOCKED = "blocked"


class OutcomeKind(str, Enum):
    """The three outcomes a Workstream function may report for one attempt."""

    SUCCESS = "success"
    RETRY = "retry"
    FAILURE = "failure"


class DependencyMode(str, Enum):
    """Whether dependencies must succeed or merely reach a terminal state."""

    SUCCESS = "success"
    TERMINAL = "terminal"


TERMINAL_STATUSES = frozenset(
    {
        WorkstreamStatus.SUCCEEDED,
        WorkstreamStatus.FAILED,
        WorkstreamStatus.CANCELLED,
        WorkstreamStatus.SKIPPED,
        WorkstreamStatus.BUDGET_EXHAUSTED,
        WorkstreamStatus.BLOCKED,
    }
)


@dataclass(frozen=True)
class WorkstreamOutcome:
    """Result of one Workstream attempt.

    ``payload`` may contain evidence produced before a retryable or fatal
    failure.  Every attempt is retained in the final run, so partial evidence
    is not discarded.
    """

    kind: OutcomeKind
    payload: Any = None
    reason: str | None = None
    reliable_veto: bool = False

    @classmethod
    def success(
        cls, payload: Any = None, *, reliable_veto: bool = False
    ) -> WorkstreamOutcome:
        return cls(OutcomeKind.SUCCESS, payload=payload, reliable_veto=reliable_veto)

    @classmethod
    def retry(cls, reason: str, payload: Any = None) -> WorkstreamOutcome:
        return cls(OutcomeKind.RETRY, payload=payload, reason=reason)

    @classmethod
    def failure(cls, reason: str, payload: Any = None) -> WorkstreamOutcome:
        return cls(OutcomeKind.FAILURE, payload=payload, reason=reason)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, OutcomeKind):
            raise TypeError("kind must be an OutcomeKind")
        if self.reliable_veto and self.kind is not OutcomeKind.SUCCESS:
            raise ValueError("only a successful outcome may establish a reliable veto")
        if self.kind in {OutcomeKind.RETRY, OutcomeKind.FAILURE} and not self.reason:
            raise ValueError(f"{self.kind.value} outcome requires a reason")


class RetryableWorkstreamError(Exception):
    """Explicitly ask the scheduler to apply the Workstream retry policy."""

    def __init__(self, reason: str, *, payload: Any = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.payload = payload


@dataclass(frozen=True)
class ActivationDecision:
    """Typed result of a conditional/adaptive activation predicate."""

    active: bool
    reason: str | None = None

    @classmethod
    def run(cls, reason: str | None = None) -> ActivationDecision:
        return cls(True, reason)

    @classmethod
    def skip(cls, reason: str) -> ActivationDecision:
        return cls(False, reason)

    def __post_init__(self) -> None:
        if not self.active and not self.reason:
            raise ValueError("an inactive Workstream requires a reason")


@dataclass(frozen=True)
class WorkstreamView:
    """Immutable state exposed to activation predicates and Workstream code."""

    workstream_id: str
    question_id: str
    status: WorkstreamStatus
    attempt_count: int
    outcome: WorkstreamOutcome | None


@dataclass(frozen=True)
class RunSnapshot:
    """Stable view of committed state at the start of a scheduling wave."""

    workstreams: Mapping[str, WorkstreamView]
    budget_limit: float
    budget_spent: float
    reliable_vetoes: tuple[str, ...]

    @property
    def budget_remaining(self) -> float:
        return self.budget_limit - self.budget_spent

    def outcome(self, workstream_id: str) -> WorkstreamOutcome | None:
        return self.workstreams[workstream_id].outcome


@dataclass(frozen=True)
class WorkstreamContext:
    """Context passed to one Workstream attempt."""

    workstream_id: str
    question_id: str
    attempt: int
    shared: Mapping[str, Any]
    snapshot: RunSnapshot
    _cancelled: threading.Event = field(repr=False, compare=False)

    def cancelled(self) -> bool:
        """Return whether a reliable veto cancelled this Workstream."""

        return self._cancelled.is_set()


WorkstreamFunction = Callable[[WorkstreamContext], WorkstreamOutcome | Any]
ActivationPredicate = Callable[[RunSnapshot], ActivationDecision | bool]


@dataclass(frozen=True)
class Workstream:
    """A question-owned node in the Expedition DAG.

    ``cost_per_attempt`` is reserved before an attempt starts and is charged
    even when that attempt fails.  This conservative rule guarantees the run
    never crosses ``budget_limit``.
    """

    workstream_id: str
    question_id: str
    run: WorkstreamFunction = field(repr=False, compare=False)
    depends_on: tuple[str, ...] = ()
    dependency_mode: DependencyMode = DependencyMode.SUCCESS
    max_attempts: int = 1
    cost_per_attempt: float = 0
    cancel_on_veto: bool = True
    activate_when: ActivationPredicate | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not self.workstream_id or not self.workstream_id.strip():
            raise ValueError("workstream_id must be non-empty")
        if not self.question_id or not self.question_id.strip():
            raise ValueError("question_id must be non-empty")
        if not callable(self.run):
            raise TypeError("run must be callable")
        if not isinstance(self.dependency_mode, DependencyMode):
            raise TypeError("dependency_mode must be a DependencyMode")
        if self.activate_when is not None and not callable(self.activate_when):
            raise TypeError("activate_when must be callable")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if not math.isfinite(self.cost_per_attempt) or self.cost_per_attempt < 0:
            raise ValueError("cost_per_attempt must be a finite non-negative number")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError(f"{self.workstream_id} has duplicate dependencies")


@dataclass(frozen=True)
class AttemptRecord:
    attempt: int
    cost: float
    outcome: WorkstreamOutcome

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "cost": self.cost,
            "kind": self.outcome.kind.value,
            "payload": self.outcome.payload,
            "reason": self.outcome.reason,
            "reliable_veto": self.outcome.reliable_veto,
        }


@dataclass(frozen=True)
class StateTransition:
    sequence: int
    workstream_id: str
    from_status: WorkstreamStatus
    to_status: WorkstreamStatus
    attempt: int
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "workstream_id": self.workstream_id,
            "from": self.from_status.value,
            "to": self.to_status.value,
            "attempt": self.attempt,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class WorkstreamRecord:
    workstream_id: str
    question_id: str
    status: WorkstreamStatus
    attempts: tuple[AttemptRecord, ...]
    outcome: WorkstreamOutcome | None
    reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.workstream_id,
            "question_id": self.question_id,
            "status": self.status.value,
            "attempt_count": len(self.attempts),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "outcome": None
            if self.outcome is None
            else {
                "kind": self.outcome.kind.value,
                "payload": self.outcome.payload,
                "reason": self.outcome.reason,
                "reliable_veto": self.outcome.reliable_veto,
            },
            "reason": self.reason,
        }


@dataclass(frozen=True)
class OrchestrationResult:
    """Complete deterministic trace of one bounded orchestration run."""

    workstreams: tuple[WorkstreamRecord, ...]
    transitions: tuple[StateTransition, ...]
    budget_limit: float
    budget_spent: float
    reliable_vetoes: tuple[str, ...]

    @property
    def budget_remaining(self) -> float:
        return self.budget_limit - self.budget_spent

    @property
    def budget_exhausted(self) -> bool:
        return any(
            row.status is WorkstreamStatus.BUDGET_EXHAUSTED
            for row in self.workstreams
        )

    def record(self, workstream_id: str) -> WorkstreamRecord:
        for row in self.workstreams:
            if row.workstream_id == workstream_id:
                return row
        raise KeyError(workstream_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workstreams": [row.to_dict() for row in self.workstreams],
            "transitions": [row.to_dict() for row in self.transitions],
            "budget": {
                "limit": self.budget_limit,
                "spent": self.budget_spent,
                "remaining": self.budget_remaining,
                "exhausted": self.budget_exhausted,
            },
            "reliable_vetoes": list(self.reliable_vetoes),
        }


@dataclass
class _MutableRecord:
    spec: Workstream
    status: WorkstreamStatus = WorkstreamStatus.PENDING
    attempts: list[AttemptRecord] = field(default_factory=list)
    outcome: WorkstreamOutcome | None = None
    reason: str | None = None
    activation_evaluated: bool = False
    cancelled: threading.Event = field(default_factory=threading.Event)


def run_workstreams(
    workstreams: Sequence[Workstream],
    *,
    max_workers: int = 4,
    budget_limit: float = math.inf,
    shared: Mapping[str, Any] | None = None,
    on_transition: Callable[[StateTransition, RunSnapshot], None] | None = None,
) -> OrchestrationResult:
    """Run a Workstream DAG with deterministic admission and commit ordering.

    Independent ready Workstreams run concurrently, at most ``max_workers`` at
    a time.  A retry consumes another declared per-attempt cost.  Conditional
    Workstreams are evaluated exactly once, after their dependencies are ready.

    Unexpected exceptions become typed fatal failures.  Raise
    :class:`RetryableWorkstreamError` or return :meth:`WorkstreamOutcome.retry`
    when bounded retry is appropriate.
    """

    specs = tuple(workstreams)
    _validate_graph(specs)
    if max_workers < 1:
        raise ValueError("max_workers must be at least one")
    if math.isnan(budget_limit) or budget_limit < 0:
        raise ValueError("budget_limit must be non-negative")

    records = [_MutableRecord(spec) for spec in specs]
    by_id = {record.spec.workstream_id: record for record in records}
    shared_view = MappingProxyType(dict(shared or {}))
    transitions: list[StateTransition] = []
    reliable_vetoes: list[str] = []
    budget_spent = 0.0

    def transition(
        record: _MutableRecord,
        status: WorkstreamStatus,
        reason: str | None = None,
    ) -> None:
        nonlocal transitions
        previous = record.status
        record.status = status
        record.reason = reason
        transitions.append(
            StateTransition(
                sequence=len(transitions) + 1,
                workstream_id=record.spec.workstream_id,
                from_status=previous,
                to_status=status,
                attempt=(
                    len(record.attempts) + 1
                    if status
                    in {
                        WorkstreamStatus.READY,
                        WorkstreamStatus.RUNNING,
                        WorkstreamStatus.BUDGET_EXHAUSTED,
                    }
                    else len(record.attempts)
                ),
                reason=reason,
            )
        )
        if on_transition is not None:
            on_transition(transitions[-1], snapshot())

    def snapshot() -> RunSnapshot:
        views = {
            row.spec.workstream_id: WorkstreamView(
                workstream_id=row.spec.workstream_id,
                question_id=row.spec.question_id,
                status=row.status,
                attempt_count=len(row.attempts),
                outcome=row.outcome,
            )
            for row in records
        }
        return RunSnapshot(
            workstreams=MappingProxyType(views),
            budget_limit=budget_limit,
            budget_spent=budget_spent,
            reliable_vetoes=tuple(reliable_vetoes),
        )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        while any(row.status not in TERMINAL_STATUSES for row in records):
            made_progress = False

            # Reliable hard gates cancel only work not already admitted to a
            # prior wave.  Exempt witness/reconciliation Workstreams continue.
            if reliable_vetoes:
                for row in records:
                    if (
                        row.status not in TERMINAL_STATUSES
                        and row.spec.cancel_on_veto
                    ):
                        row.cancelled.set()
                        transition(
                            row,
                            WorkstreamStatus.CANCELLED,
                            f"reliable veto from {reliable_vetoes[0]} made this "
                            "moot; its question stays in the official follow-ups",
                        )
                        made_progress = True

            # Resolve dependency failures and conditionally activate nodes.
            for row in records:
                if row.status not in {
                    WorkstreamStatus.PENDING,
                    WorkstreamStatus.RETRY_PENDING,
                }:
                    continue
                dependencies = [by_id[dep] for dep in row.spec.depends_on]
                if any(dep.status not in TERMINAL_STATUSES for dep in dependencies):
                    continue
                if (
                    row.spec.dependency_mode is DependencyMode.SUCCESS
                    and any(
                        dep.status is not WorkstreamStatus.SUCCEEDED
                        for dep in dependencies
                    )
                ):
                    failed = next(
                        dep.spec.workstream_id
                        for dep in dependencies
                        if dep.status is not WorkstreamStatus.SUCCEEDED
                    )
                    transition(
                        row,
                        WorkstreamStatus.BLOCKED,
                        f"dependency {failed} did not succeed",
                    )
                    made_progress = True
                    continue
                if not row.activation_evaluated:
                    row.activation_evaluated = True
                    if row.spec.activate_when is not None:
                        try:
                            decision = row.spec.activate_when(snapshot())
                            if isinstance(decision, bool):
                                decision = (
                                    ActivationDecision.run()
                                    if decision
                                    else ActivationDecision.skip(
                                        "activation predicate returned false"
                                    )
                                )
                            if not isinstance(decision, ActivationDecision):
                                raise TypeError(
                                    "activation predicate must return "
                                    "ActivationDecision or bool"
                                )
                        except Exception as exc:  # predicate is caller code
                            transition(
                                row,
                                WorkstreamStatus.FAILED,
                                f"activation failed: {type(exc).__name__}",
                            )
                            made_progress = True
                            continue
                        if not decision.active:
                            transition(
                                row,
                                WorkstreamStatus.SKIPPED,
                                decision.reason,
                            )
                            made_progress = True
                            continue
                transition(row, WorkstreamStatus.READY)
                made_progress = True

            # Admission is declaration ordered.  A node that cannot afford its
            # next attempt is terminal, but later cheaper nodes may still run.
            wave: list[_MutableRecord] = []
            for row in records:
                if row.status is not WorkstreamStatus.READY:
                    continue
                cost = row.spec.cost_per_attempt
                if budget_spent + cost > budget_limit:
                    transition(
                        row,
                        WorkstreamStatus.BUDGET_EXHAUSTED,
                        "insufficient budget for next attempt",
                    )
                    made_progress = True
                    continue
                if len(wave) >= max_workers:
                    continue
                budget_spent += cost
                transition(row, WorkstreamStatus.RUNNING)
                wave.append(row)
                made_progress = True

            if wave:
                attempt_snapshot = snapshot()
                futures = []
                for row in wave:
                    context = WorkstreamContext(
                        workstream_id=row.spec.workstream_id,
                        question_id=row.spec.question_id,
                        attempt=len(row.attempts) + 1,
                        shared=shared_view,
                        snapshot=attempt_snapshot,
                        _cancelled=row.cancelled,
                    )
                    futures.append((row, pool.submit(_run_attempt, row.spec, context)))

                # Waiting for the full wave makes commit order independent of
                # thread timing while preserving actual concurrent execution.
                completed = [(row, future.result()) for row, future in futures]
                for row, outcome in completed:
                    attempt = AttemptRecord(
                        attempt=len(row.attempts) + 1,
                        cost=row.spec.cost_per_attempt,
                        outcome=outcome,
                    )
                    row.attempts.append(attempt)
                    row.outcome = outcome
                    if outcome.kind is OutcomeKind.SUCCESS:
                        transition(row, WorkstreamStatus.SUCCEEDED, outcome.reason)
                        if outcome.reliable_veto:
                            reliable_vetoes.append(row.spec.workstream_id)
                    elif outcome.kind is OutcomeKind.RETRY:
                        if len(row.attempts) < row.spec.max_attempts:
                            transition(
                                row, WorkstreamStatus.RETRY_PENDING, outcome.reason
                            )
                        else:
                            transition(
                                row,
                                WorkstreamStatus.FAILED,
                                f"retry limit reached: {outcome.reason}",
                            )
                    else:
                        transition(row, WorkstreamStatus.FAILED, outcome.reason)

            if not made_progress:
                # Graph validation excludes cycles, so this is a defensive
                # invariant rather than a normal completion path.
                unresolved = ", ".join(
                    row.spec.workstream_id
                    for row in records
                    if row.status not in TERMINAL_STATUSES
                )
                raise RuntimeError(f"orchestration made no progress: {unresolved}")

    final_records = tuple(
        WorkstreamRecord(
            workstream_id=row.spec.workstream_id,
            question_id=row.spec.question_id,
            status=row.status,
            attempts=tuple(row.attempts),
            outcome=row.outcome,
            reason=row.reason,
        )
        for row in records
    )
    return OrchestrationResult(
        workstreams=final_records,
        transitions=tuple(transitions),
        budget_limit=budget_limit,
        budget_spent=budget_spent,
        reliable_vetoes=tuple(reliable_vetoes),
    )


def _run_attempt(
    spec: Workstream, context: WorkstreamContext
) -> WorkstreamOutcome:
    try:
        result = spec.run(context)
        if isinstance(result, WorkstreamOutcome):
            return result
        return WorkstreamOutcome.success(result)
    except RetryableWorkstreamError as exc:
        return WorkstreamOutcome.retry(exc.reason, payload=exc.payload)
    except Exception as exc:  # provider/adapter failure becomes typed state
        return WorkstreamOutcome.failure(type(exc).__name__)


def _validate_graph(specs: tuple[Workstream, ...]) -> None:
    ids = [spec.workstream_id for spec in specs]
    if len(set(ids)) != len(ids):
        duplicate = next(workstream_id for workstream_id in ids if ids.count(workstream_id) > 1)
        raise ValueError(f"duplicate Workstream id {duplicate}")
    known = set(ids)
    for spec in specs:
        for dependency in spec.depends_on:
            if dependency not in known:
                raise ValueError(
                    f"{spec.workstream_id} has unknown dependency {dependency}"
                )
            if dependency == spec.workstream_id:
                raise ValueError(f"{spec.workstream_id} cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()
    by_id = {spec.workstream_id: spec for spec in specs}

    def visit(workstream_id: str) -> None:
        if workstream_id in visiting:
            raise ValueError(f"Workstream dependency cycle includes {workstream_id}")
        if workstream_id in visited:
            return
        visiting.add(workstream_id)
        for dependency in by_id[workstream_id].depends_on:
            visit(dependency)
        visiting.remove(workstream_id)
        visited.add(workstream_id)

    for workstream_id in ids:
        visit(workstream_id)
