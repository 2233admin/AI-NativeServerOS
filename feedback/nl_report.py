"""Generate natural language reports from execution results."""

from __future__ import annotations


def format_report(
    task_id: str,
    skill: str,
    target: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    duration_ms: int,
    changed: bool,
) -> str:
    """Generate a human-readable NL report of execution results.

    Phase 1: Template-based. Phase 2+: LLM-generated summaries.
    """
    status = "successfully" if exit_code == 0 else "with errors"

    action_verbs = {
        "install_package": "installed",
        "edit_file": "edited",
        "restart_service": "restarted",
        "run_command": "executed",
        "check_status": "checked",
    }
    verb = action_verbs.get(skill, "processed")

    report = f"Task {task_id}: {verb} '{target}' {status} in {duration_ms}ms."

    if changed:
        report += " System state was modified."
    else:
        report += " No changes were made."

    if exit_code != 0 and stderr:
        short_err = stderr.strip().split("\n")[0][:100]
        report += f"\nError: {short_err}"

    return report
