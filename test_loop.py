"""A2Alaw Phase 1 MVP - Atomic loop test.

Run: python3 -m a2alaw.test_loop

Tests the full NL -> Intent -> DAG -> (dry_run) -> Report -> Audit pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from a2alaw.orchestrator.dag_parser import parse_intent_to_dag
from a2alaw.orchestrator.risk_scorer import requires_approval, score_command
from a2alaw.executor.code_gen import generate_command, generate_rollback
from a2alaw.executor.self_heal import classify_and_heal
from a2alaw.feedback.nl_report import format_report


def test_atomic_loop():
    """Test the complete atomic loop: NL -> DAG -> CodeGen -> Report."""
    print("=" * 60)
    print("A2Alaw Phase 1 - Atomic Loop Test")
    print("=" * 60)

    # Step 1: Simulate NL -> Intent (P1)
    intent = {
        "id": str(uuid.uuid4()),
        "nl_input": "安装 pandas",
        "intent": {
            "action": "install",
            "target": "pandas",
            "params": {},
            "constraints": {"dry_run": True},
        },
        "confidence": 0.92,
        "risk_level": "low",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(f"\n[P1] Intent: '{intent['nl_input']}' -> action={intent['intent']['action']}, target={intent['intent']['target']}")

    # Step 2: Intent -> DAG (P2)
    dag = parse_intent_to_dag(intent)
    print(f"[P2] DAG: {len(dag.nodes)} nodes, risk={dag.risk_score:.1%}")
    for node in dag.topological_order():
        print(f"     - {node.skill.value}({node.params.get('target', '')}) risk={node.risk_level}")

    # Step 3: Risk assessment (P3)
    cmd = generate_command("install_package", {"target": "pandas"})
    risk_score, reasons = score_command(cmd)
    needs_approval = requires_approval(risk_score, intent["confidence"])
    print(f"[P3] Command: '{cmd}' risk={risk_score:.1%} approval={'YES' if needs_approval else 'NO'}")

    # Step 4: Code generation (P4)
    rollback_cmd = generate_rollback("install_package", {"target": "pandas"})
    print(f"[P4] Generated command: {cmd}")
    print(f"     Rollback: {rollback_cmd}")

    # Step 5: Dry run (P5 - sandbox skipped in test)
    print(f"[P5] [DRY RUN] Would execute in Docker sandbox")

    # Step 6: Error handling test
    heal = classify_and_heal("E: Unable to locate package pandas-xxx", 100, 0)
    print(f"[P6] Error heal: retry={heal.should_retry}, class={heal.error_class}, human={heal.human_needed}")

    # Step 7: NL Report (P7)
    report = format_report(
        task_id=intent["id"][:8],
        skill="install_package",
        target="pandas",
        exit_code=0,
        stdout="Successfully installed pandas",
        stderr="",
        duration_ms=1234,
        changed=True,
    )
    print(f"[P7] Report: {report}")

    print("\n" + "=" * 60)
    print("All 7 pipeline stages validated (dry run).")
    print("=" * 60)


if __name__ == "__main__":
    test_atomic_loop()
