"""Self-Healer — automatic repair of down peers.

Ring repair topology: central→sv→tokyo→central.
Each node is responsible for repairing the NEXT node in the ring.
If the repairer itself is down, the third node takes over (quorum of 2).

Repair protocol:
1. Detect peer DOWN (3 missed heartbeats = 90s)
2. SSH into peer, run diagnostic
3. Attempt automatic fix (restart services, clear disk, etc.)
4. If fix fails, escalate to mesh:discussion for peer vote
5. Report result to mesh:health stream
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from a2alaw.executor.remote import execute_on_node
from a2alaw.executor.host import HostResult
from a2alaw.mesh.peer import Node, whoami, repair_target, peers, REPAIR_RING


class RepairAction(Enum):
    RESTART_DAEMON = "restart_daemon"
    RESTART_WIREGUARD = "restart_wireguard"
    CLEAR_DISK = "clear_disk"
    RESTART_REDIS = "restart_redis"
    REBOOT = "reboot"


# Diagnostic script — runs on the sick node to figure out what's wrong
DIAGNOSE_SCRIPT = r"""#!/bin/bash
set -uo pipefail
echo "=== DIAG START ==="

# Check disk
DISK_PCT=$(df / --output=pcent | tail -1 | tr -d ' %')
echo "DISK_PCT=$DISK_PCT"
[ "$DISK_PCT" -gt 95 ] && echo "ISSUE:disk_full"

# Check a2alawd
systemctl is-active a2alawd >/dev/null 2>&1 || echo "ISSUE:daemon_down"

# Check WireGuard
ip link show wg0 >/dev/null 2>&1 || echo "ISSUE:wireguard_down"

# Check Redis (central only)
if systemctl list-unit-files | grep -q redis-server; then
    systemctl is-active redis-server >/dev/null 2>&1 || echo "ISSUE:redis_down"
fi

# Check memory
FREE_MB=$(free -m | awk '/^Mem:/{print $7}')
echo "FREE_MB=$FREE_MB"
[ "$FREE_MB" -lt 100 ] && echo "ISSUE:low_memory"

echo "=== DIAG END ==="
"""

# Repair scripts for each issue
REPAIR_SCRIPTS = {
    "daemon_down": "systemctl restart a2alawd && sleep 2 && systemctl is-active a2alawd",
    "wireguard_down": "systemctl restart wg-quick@wg0 && sleep 2 && wg show wg0",
    "redis_down": "systemctl restart redis-server && sleep 2 && redis-cli ping",
    "disk_full": (
        "journalctl --vacuum-size=50M 2>/dev/null; "
        "apt-get clean 2>/dev/null; "
        "find /tmp -type f -mtime +7 -delete 2>/dev/null; "
        "df -h /"
    ),
    "low_memory": (
        "sync && echo 3 > /proc/sys/vm/drop_caches; "
        "free -m"
    ),
}


@dataclass
class RepairResult:
    node: str
    issues: list[str]
    fixed: list[str]
    failed: list[str]
    duration_ms: int


def diagnose(node: Node) -> list[str]:
    """SSH into node, run diagnostic, return list of issues."""
    result = execute_on_node(node.name, DIAGNOSE_SCRIPT, timeout_s=30)
    if result.exit_code != 0 and not result.stdout:
        return ["unreachable"]

    issues = []
    for line in result.stdout.splitlines():
        if line.startswith("ISSUE:"):
            issues.append(line.split(":", 1)[1])
    return issues


def repair_node(node: Node, issues: list[str]) -> RepairResult:
    """Attempt to fix detected issues on a peer node."""
    start = time.time()
    fixed = []
    failed = []

    for issue in issues:
        if issue == "unreachable":
            failed.append(issue)
            continue

        script = REPAIR_SCRIPTS.get(issue)
        if not script:
            failed.append(issue)
            continue

        result = execute_on_node(node.name, script, timeout_s=60)
        if result.exit_code == 0:
            fixed.append(issue)
        else:
            failed.append(issue)

    duration = int((time.time() - start) * 1000)
    return RepairResult(
        node=node.name,
        issues=issues,
        fixed=fixed,
        failed=failed,
        duration_ms=duration,
    )


def auto_heal(event_bus=None) -> RepairResult | None:
    """Check my repair target; if down, diagnose and fix.

    Returns RepairResult if repair was attempted, None if target is healthy.
    """
    me = whoami()
    target = repair_target()

    # Quick health check first
    from a2alaw.mesh.heartbeat import HeartbeatMonitor
    monitor = HeartbeatMonitor()
    alive = monitor.check_peer(target)
    if alive:
        return None

    # Target is down — diagnose
    issues = diagnose(target)
    if not issues:
        return None

    # Repair
    result = repair_node(target, issues)

    # Report to mesh
    if event_bus:
        try:
            event_bus.publish("mesh:health", {
                "reporter": me.name,
                "action": "repair",
                "target": target.name,
                "issues": str(issues),
                "fixed": str(result.fixed),
                "failed": str(result.failed),
                "duration_ms": result.duration_ms,
            })
        except Exception:
            pass

    return result
