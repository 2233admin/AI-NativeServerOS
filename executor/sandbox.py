"""P5: Docker sandbox execution with seccomp and resource limits."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    changed: bool = False


SECCOMP_PROFILE = Path(__file__).parent.parent / "safety" / "seccomp.json"


def run_in_sandbox(
    command: str,
    *,
    dry_run: bool = False,
    timeout_s: int = 30,
    memory_mb: int = 200,
    network: bool = True,
    writable: bool = False,
) -> SandboxResult:
    """Execute a command inside a Docker sandbox.

    Args:
        command: Shell command to execute
        dry_run: If True, only print what would be executed
        timeout_s: Maximum execution time
        memory_mb: Memory limit
        network: Whether to allow network access
    """
    if dry_run:
        return SandboxResult(
            exit_code=0,
            stdout=f"[DRY RUN] Would execute: {command}",
            stderr="",
            duration_ms=0,
        )

    docker_cmd = [
        "docker", "run", "--rm",
        "--memory", f"{memory_mb}m",
        "--cpus", "1",
        "--pids-limit", "100",
        "--tmpfs", "/tmp:size=50m",
        "--security-opt", f"seccomp={SECCOMP_PROFILE}",
    ]

    if not writable:
        docker_cmd.insert(docker_cmd.index("--tmpfs"), "--read-only")

    if not network:
        docker_cmd.extend(["--network", "none"])

    docker_cmd.extend([
        "debian:12-slim",
        "bash", "-c", command,
    ])

    start = time.monotonic()
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        duration = int((time.monotonic() - start) * 1000)
        return SandboxResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=duration,
            changed=result.returncode == 0,
        )
    except subprocess.TimeoutExpired:
        duration = int((time.monotonic() - start) * 1000)
        return SandboxResult(
            exit_code=124,
            stdout="",
            stderr=f"Command timed out after {timeout_s}s",
            duration_ms=duration,
        )
