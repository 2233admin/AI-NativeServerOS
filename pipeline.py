"""A2Alaw Pipeline Runner - orchestrates the full NL -> System Change -> Audit loop.

This is the core execution engine that chains all 7 pipeline stages:
  P1: NL -> Intent (nl_parser)
  P2: Intent -> DAG (dag_parser)
  P3: Risk Assessment (risk_scorer)
  P4: Code Generation (code_gen)
  P5: Sandbox Execution (sandbox)
  P6: Error Handling (self_heal)
  P7: Report + Audit (nl_report + git_audit)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from a2alaw.orchestrator.nl_parser import ParsedIntent, parse_nl
from a2alaw.orchestrator.dag_parser import parse_intent_to_dag, ExecutionDAG, DAGNode
from a2alaw.orchestrator.risk_scorer import requires_approval, score_command
from a2alaw.executor.code_gen import generate_command, generate_rollback
from a2alaw.executor.sandbox import run_in_sandbox, SandboxResult
from a2alaw.executor.self_heal import classify_and_heal, MAX_RETRIES
from a2alaw.feedback.nl_report import format_report
from a2alaw.safety.git_audit import record_change


@dataclass
class PipelineResult:
    intent: ParsedIntent
    dag: ExecutionDAG
    approved: bool = False
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
    ):
        self.dry_run = dry_run
        self.auto_approve_low_risk = auto_approve_low_risk
        self.approval_fn = approval_fn  # callable(action, target, risk) -> bool

    def run(self, nl_input: str) -> PipelineResult:
        """Execute the full pipeline for a natural language command."""
        start = time.monotonic()

        # P1: NL -> Intent
        intent = parse_nl(nl_input)

        # P2: Intent -> DAG
        dag = parse_intent_to_dag(intent.to_dict())

        result = PipelineResult(intent=intent, dag=dag)

        # P3: Risk check + approval
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

        # Execute DAG nodes in topological order
        for node in dag.topological_order():
            node_result = self._execute_node(node)
            result.results.append(node_result)

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
            except Exception:
                pass  # Audit failure is non-fatal

        result.total_ms = int((time.monotonic() - start) * 1000)
        return result

    def _execute_node(self, node: DAGNode) -> dict[str, Any]:
        """Execute a single DAG node with retry logic."""
        # P4: Code generation
        command = generate_command(
            node.skill.value,
            node.params,
        )
        rollback = generate_rollback(node.skill.value, node.params)

        # P5: Sandbox execution with P6: retry loop
        for attempt in range(MAX_RETRIES + 1):
            needs_write = node.skill.value in ("install_package", "edit_file")
            sandbox_result = run_in_sandbox(
                command,
                dry_run=self.dry_run,
                network=node.skill.value == "install_package",
                writable=needs_write,
            )

            if sandbox_result.exit_code == 0:
                return {
                    "node_id": node.id,
                    "skill": node.skill.value,
                    "command": command,
                    "rollback": rollback,
                    "exit_code": sandbox_result.exit_code,
                    "stdout": sandbox_result.stdout,
                    "stderr": sandbox_result.stderr,
                    "duration_ms": sandbox_result.duration_ms,
                    "changed": sandbox_result.changed,
                    "attempt": attempt + 1,
                }

            # P6: Error classification + heal
            heal = classify_and_heal(
                sandbox_result.stderr,
                sandbox_result.exit_code,
                attempt,
            )

            if not heal.should_retry:
                return {
                    "node_id": node.id,
                    "skill": node.skill.value,
                    "command": command,
                    "rollback": rollback,
                    "exit_code": sandbox_result.exit_code,
                    "stdout": sandbox_result.stdout,
                    "stderr": sandbox_result.stderr,
                    "duration_ms": sandbox_result.duration_ms,
                    "changed": False,
                    "attempt": attempt + 1,
                    "error_class": heal.error_class.value,
                    "human_needed": heal.human_needed,
                }

        # Should not reach here, but safety net
        return {
            "node_id": node.id,
            "skill": node.skill.value,
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Max retries exhausted",
            "duration_ms": 0,
            "changed": False,
        }
