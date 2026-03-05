"""A2Alaw Pipeline Runner - orchestrates the full NL -> System Change -> Audit loop.

This is the core execution engine that chains all 7 pipeline stages:
  P1: NL -> Intent (nl_parser)
  P2: Intent -> DAG (dag_parser)
  P3: OPA Policy + Risk Assessment
  P4: Code Generation (code_gen)
  P5: Host Execution (host) — real system changes, sandbox for dry-run only
  P6: Error Handling (self_heal)
  P7: Report + Audit (nl_report + git_audit + redis streams)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from a2alaw.orchestrator.nl_parser import ParsedIntent, parse_nl
from a2alaw.orchestrator.dag_parser import parse_intent_to_dag, ExecutionDAG, DAGNode
from a2alaw.orchestrator.risk_scorer import requires_approval, score_command
from a2alaw.executor.code_gen import generate_command, generate_rollback
from a2alaw.executor.host import execute_on_host, dry_run_preview, HostResult
from a2alaw.executor.self_heal import classify_and_heal, MAX_RETRIES
from a2alaw.feedback.nl_report import format_report
from a2alaw.safety.git_audit import record_change
from a2alaw.safety.opa_client import evaluate as opa_evaluate


@dataclass
class PipelineResult:
    intent: ParsedIntent
    dag: ExecutionDAG
    approved: bool = False
    policy_blocked: bool = False
    policy_reasons: list[str] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    report: str = ""
    audit_sha: str | None = None
    total_ms: int = 0

    @property
    def success(self) -> bool:
        return all(r.get("exit_code") == 0 for r in self.results)


class Pipeline:
    """Main A2Alaw execution pipeline."""

    def __init__(
        self,
        *,
        dry_run: bool = False,
        auto_approve_low_risk: bool = True,
        approval_fn=None,
        event_bus=None,
        use_agent: bool = False,
    ):
        self.dry_run = dry_run
        self.auto_approve_low_risk = auto_approve_low_risk
        self.approval_fn = approval_fn
        self.event_bus = event_bus
        self.use_agent = use_agent  # Use smolagents for multi-step planning

    def run(self, nl_input: str) -> PipelineResult:
        """Execute the full pipeline for a natural language command."""
        start = time.monotonic()

        # P1+P2: NL -> Intent + DAG
        if self.use_agent:
            try:
                from a2alaw.orchestrator.agent import plan_multi_step
                intent, dag = plan_multi_step(nl_input)
            except Exception:
                intent = parse_nl(nl_input)
                dag = None
        else:
            intent = parse_nl(nl_input)
        self._emit("user:intent", {
            "id": intent.id,
            "nl_input": intent.nl_input,
            "session_id": "cli",
            "timestamp": intent.timestamp,
        })

        # P2: Intent -> DAG (skip if agent already built it)
        if not self.use_agent or dag is None:
            dag = parse_intent_to_dag(intent.to_dict())

        result = PipelineResult(intent=intent, dag=dag)

        # P3: OPA policy check
        first_cmd = generate_command(
            dag.topological_order()[-1].skill.value,
            dag.topological_order()[-1].params,
        ) if dag.nodes else ""

        policy = opa_evaluate(
            action=intent.action,
            target=intent.target,
            command=first_cmd,
            risk_level=intent.risk_level,
            confidence=intent.confidence,
        )

        if policy.blocked:
            result.policy_blocked = True
            result.policy_reasons = policy.deny_reasons
            reason = "; ".join(policy.deny_reasons) if policy.deny_reasons else "Policy denied"
            result.report = f"BLOCKED by policy: {reason}"
            result.total_ms = int((time.monotonic() - start) * 1000)
            self._emit("agent:plan", {
                "intent_id": intent.id,
                "dag": "blocked",
                "risk_score": dag.risk_score,
                "requires_approval": True,
            })
            return result

        # Risk check + approval (for cases OPA allows but risk scorer flags)
        needs_approval = requires_approval(dag.risk_score, intent.confidence)
        if needs_approval:
            if self.auto_approve_low_risk and dag.risk_score < 0.3:
                result.approved = True
            elif self.approval_fn:
                result.approved = self.approval_fn(
                    intent.action, intent.target, intent.risk_level
                )
            else:
                result.approved = False
                result.report = f"Action requires approval (risk={dag.risk_score:.0%}, confidence={intent.confidence:.0%})"
                result.total_ms = int((time.monotonic() - start) * 1000)
                return result
        else:
            result.approved = True

        self._emit("agent:plan", {
            "intent_id": intent.id,
            "dag": str(dag.to_dict()),
            "risk_score": dag.risk_score,
            "requires_approval": False,
        })

        # Execute DAG nodes in topological order
        for node in dag.topological_order():
            node_result = self._execute_node(node)
            result.results.append(node_result)

            self._emit("system:logs", {
                "task_id": intent.id[:8],
                "skill": node_result.get("skill", ""),
                "status": "ok" if node_result["exit_code"] == 0 else "error",
                "stdout": node_result.get("stdout", "")[:500],
                "stderr": node_result.get("stderr", "")[:500],
                "exit_code": node_result["exit_code"],
                "duration_ms": node_result.get("duration_ms", 0),
            })

            if node_result["exit_code"] != 0:
                break

        # P7: Report
        last = result.results[-1] if result.results else {}
        result.report = format_report(
            task_id=intent.id[:8],
            skill=intent.action,
            target=intent.target,
            exit_code=last.get("exit_code", -1),
            stdout=last.get("stdout", ""),
            stderr=last.get("stderr", ""),
            duration_ms=last.get("duration_ms", 0),
            changed=last.get("changed", False),
        )

        self._emit("agent:report", {
            "task_id": intent.id[:8],
            "summary_nl": result.report,
            "changed": last.get("changed", False),
            "rollback_available": bool(last.get("rollback")),
        })

        # Git audit (skip in dry run)
        if not self.dry_run and result.success:
            try:
                result.audit_sha = record_change(
                    task_id=intent.id[:8],
                    skill=intent.action,
                    target=intent.target,
                    command=last.get("command", ""),
                    stdout=last.get("stdout", "")[:500],
                    exit_code=last.get("exit_code", 0),
                )
                if result.audit_sha:
                    self._emit("agent:audit", {
                        "task_id": intent.id[:8],
                        "commit_sha": result.audit_sha,
                        "diff_summary": f"[{intent.action}] {intent.target}",
                        "author": "a2alaw",
                        "timestamp": intent.timestamp,
                    })
            except Exception:
                pass

        result.total_ms = int((time.monotonic() - start) * 1000)
        return result

    def _execute_node(self, node: DAGNode) -> dict[str, Any]:
        """Execute a single DAG node with retry logic.

        Uses host execution by default (real system changes).
        Only uses dry-run preview when self.dry_run is True.
        """
        script = generate_command(node.skill.value, node.params)
        rollback = generate_rollback(node.skill.value, node.params)

        for attempt in range(MAX_RETRIES + 1):
            if self.dry_run:
                hr = dry_run_preview(script)
            else:
                hr = execute_on_host(script)

            if hr.exit_code == 0:
                return {
                    "node_id": node.id,
                    "skill": node.skill.value,
                    "command": script,
                    "rollback": rollback,
                    "exit_code": hr.exit_code,
                    "stdout": hr.stdout,
                    "stderr": hr.stderr,
                    "duration_ms": hr.duration_ms,
                    "changed": hr.changed,
                    "attempt": attempt + 1,
                }

            heal = classify_and_heal(hr.stderr, hr.exit_code, attempt)

            if not heal.should_retry:
                return {
                    "node_id": node.id,
                    "skill": node.skill.value,
                    "command": script,
                    "rollback": rollback,
                    "exit_code": hr.exit_code,
                    "stdout": hr.stdout,
                    "stderr": hr.stderr,
                    "duration_ms": hr.duration_ms,
                    "changed": False,
                    "attempt": attempt + 1,
                    "error_class": heal.error_class.value,
                    "human_needed": heal.human_needed,
                }

        return {
            "node_id": node.id,
            "skill": node.skill.value,
            "command": script,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Max retries exhausted",
            "duration_ms": 0,
            "changed": False,
        }

    def _emit(self, stream: str, data: dict) -> None:
        """Publish event to Redis Streams (best-effort)."""
        if not self.event_bus:
            return
        try:
            self.event_bus.publish(stream, data)
        except Exception:
            pass
