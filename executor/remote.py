"""Remote execution via SSH for multi-node mesh governance.

Central node (10.10.0.1) dispatches commands to SV/Tokyo via WireGuard mesh.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

from a2alaw.executor.host import HostResult


# Known mesh nodes
MESH_NODES = {
    "central": "10.10.0.1",
    "sv": "10.10.0.2",
    "tokyo": "10.10.0.3",
}


def execute_on_node(
    node: str,
    script: str,
    *,
    timeout_s: int = 120,
    ssh_key: str | None = None,
    user: str = "root",
) -> HostResult:
    """Execute a script on a remote node via SSH.

    Args:
        node: Node name (central/sv/tokyo) or IP address
        script: Bash script content to execute
        timeout_s: SSH timeout
        ssh_key: Path to SSH private key (default: ~/.ssh/id_rsa)
    """
    ip = MESH_NODES.get(node, node)

    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
    if ssh_key:
        ssh_cmd.extend(["-i", ssh_key])
    ssh_cmd.append(f"{user}@{ip}")
    ssh_cmd.extend(["bash", "-s"])

    start = time.monotonic()
    try:
        result = subprocess.run(
            ssh_cmd,
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout_s,
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
            stderr=f"SSH to {ip} timed out after {timeout_s}s",
            duration_ms=duration,
        )


def execute_on_all(
    script: str,
    *,
    nodes: list[str] | None = None,
    **kwargs,
) -> dict[str, HostResult]:
    """Execute on multiple nodes sequentially. Returns {node: result}."""
    targets = nodes or list(MESH_NODES.keys())
    results = {}
    for node in targets:
        results[node] = execute_on_node(node, script, **kwargs)
    return results
