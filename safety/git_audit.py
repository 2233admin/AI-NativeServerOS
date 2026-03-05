"""Git audit trail for all system changes."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

AUDIT_REPO = Path("/var/lib/a2alaw/audit")


def init_audit_repo() -> None:
    """Initialize the git audit repository."""
    AUDIT_REPO.mkdir(parents=True, exist_ok=True)
    if not (AUDIT_REPO / ".git").exists():
        subprocess.run(["git", "init"], cwd=AUDIT_REPO, check=True)
        subprocess.run(
            ["git", "config", "user.email", "a2alaw@localhost"],
            cwd=AUDIT_REPO, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "A2Alaw Audit"],
            cwd=AUDIT_REPO, check=True,
        )


def record_change(
    task_id: str,
    skill: str,
    target: str,
    command: str,
    stdout: str,
    exit_code: int,
) -> str | None:
    """Record an execution result as a git commit. Returns commit SHA."""
    init_audit_repo()

    log_file = AUDIT_REPO / "audit.log"
    entry = (
        f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
        f"Task: {task_id}\n"
        f"Skill: {skill}\n"
        f"Target: {target}\n"
        f"Command: {command}\n"
        f"Exit: {exit_code}\n"
        f"Output: {stdout[:500]}\n\n"
    )

    with open(log_file, "a") as f:
        f.write(entry)

    subprocess.run(["git", "add", "-A"], cwd=AUDIT_REPO, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", f"[{skill}] {target} (task:{task_id[:8]})"],
        cwd=AUDIT_REPO,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=AUDIT_REPO,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return sha
    return None
