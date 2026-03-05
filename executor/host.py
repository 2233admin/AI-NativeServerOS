"""P5: Host execution — direct system changes on the local machine.

A2Alaw is a server governance OS. Commands execute on the real host,
not inside Docker sandboxes. Safety is enforced by OPA policy + human
approval at the pipeline layer, not by isolation.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HostResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    changed: bool = False


def execute_on_host(
    script: str,
    *,
    timeout_s: int = 120,
    workdir: str | None = None,
    env: dict[str, str] | None = None,
) -> HostResult:
    """Execute a bash script directly on the host.

    OPA policy and human approval must be checked BEFORE calling this.
    This function does NOT perform any safety checks — it trusts its caller.
    """
    # Write script to temp file for clean execution
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".sh", prefix="a2alaw-", delete=False
    ) as f:
        f.write(script)
        script_path = f.name

    try:
        start = time.monotonic()
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=workdir,
            env=env,
        )
        duration = int((time.monotonic() - start) * 1000)
        return HostResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=duration,
            changed=result.returncode == 0,
        )
    except subprocess.TimeoutExpired:
        duration = int((time.monotonic() - start) * 1000)
        return HostResult(
            exit_code=124,
            stdout="",
            stderr=f"Command timed out after {timeout_s}s",
            duration_ms=duration,
        )
    finally:
        Path(script_path).unlink(missing_ok=True)


def dry_run_preview(script: str) -> HostResult:
    """Return a preview without executing."""
    return HostResult(
        exit_code=0,
        stdout=f"[DRY RUN] Would execute:\n{script}",
        stderr="",
        duration_ms=0,
    )
