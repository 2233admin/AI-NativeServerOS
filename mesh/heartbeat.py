"""Heartbeat — peer health monitoring via HTTP + SSH fallback.

Every node pings all peers every 30s. Health state published to
Redis Stream 'mesh:health'. Three consecutive failures trigger
repair protocol.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum

from a2alaw.mesh.peer import Node, peers, whoami, repair_target


class NodeState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"   # 1-2 missed heartbeats
    DOWN = "down"           # 3+ missed heartbeats
    REPAIRING = "repairing"


@dataclass
class PeerHealth:
    node: Node
    state: NodeState = NodeState.HEALTHY
    last_seen: float = 0.0
    miss_count: int = 0
    last_error: str = ""

    @property
    def age_s(self) -> float:
        if self.last_seen == 0:
            return float("inf")
        return time.time() - self.last_seen


MISS_THRESHOLD_DEGRADED = 1
MISS_THRESHOLD_DOWN = 3
HEARTBEAT_INTERVAL = 30  # seconds


class HeartbeatMonitor:
    """Monitors all peers via periodic health checks."""

    def __init__(self, event_bus=None):
        self.me = whoami()
        self.event_bus = event_bus
        self.health: dict[str, PeerHealth] = {
            n.name: PeerHealth(node=n) for n in peers()
        }
        self._running = False
        self._thread: threading.Thread | None = None

    def check_peer(self, node: Node) -> bool:
        """Ping a peer's /health endpoint. Returns True if healthy."""
        try:
            import httpx
            resp = httpx.get(node.health_url, timeout=5.0)
            return resp.status_code == 200
        except Exception:
            pass

        # Fallback: SSH ping
        try:
            import subprocess
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                 f"root@{node.ip}", "echo pong"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0 and "pong" in result.stdout
        except Exception:
            return False

    def tick(self):
        """Run one heartbeat cycle: check all peers, update state."""
        for name, ph in self.health.items():
            alive = self.check_peer(ph.node)

            if alive:
                ph.state = NodeState.HEALTHY
                ph.last_seen = time.time()
                ph.miss_count = 0
                ph.last_error = ""
            else:
                ph.miss_count += 1
                if ph.miss_count >= MISS_THRESHOLD_DOWN:
                    ph.state = NodeState.DOWN
                elif ph.miss_count >= MISS_THRESHOLD_DEGRADED:
                    ph.state = NodeState.DEGRADED

            self._emit_health(ph)

    def get_down_peers(self) -> list[PeerHealth]:
        return [ph for ph in self.health.values() if ph.state == NodeState.DOWN]

    def start(self):
        """Start background heartbeat thread."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            self.tick()
            time.sleep(HEARTBEAT_INTERVAL)

    def _emit_health(self, ph: PeerHealth):
        if not self.event_bus:
            return
        try:
            self.event_bus.publish("mesh:health", {
                "reporter": self.me.name,
                "node": ph.node.name,
                "state": ph.state.value,
                "miss_count": ph.miss_count,
                "last_seen": ph.last_seen,
            })
        except Exception:
            pass
