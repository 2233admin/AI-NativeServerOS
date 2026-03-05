"""Mesh Peer — node identity and peer discovery.

Every node is equal. No master. Each knows all peers and can act on any.
Ring topology for repair: central→sv→tokyo→central (circular failover).
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    ip: str
    port: int = 8741
    role: str = "peer"  # All nodes are peers

    @property
    def api_url(self) -> str:
        return f"http://{self.ip}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.api_url}/health"


# Mesh topology — all peers, ring repair order
MESH = [
    Node("central", "10.10.0.1"),
    Node("sv", "10.10.0.2"),
    Node("tokyo", "10.10.0.3"),
]

# Ring repair: each node is responsible for repairing the NEXT node
# central repairs sv, sv repairs tokyo, tokyo repairs central
REPAIR_RING = {
    "central": "sv",
    "sv": "tokyo",
    "tokyo": "central",
}


def whoami() -> Node:
    """Detect which node we are by matching local IPs."""
    local_name = os.environ.get("A2ALAW_NODE_NAME")
    if local_name:
        return next(n for n in MESH if n.name == local_name)

    # Auto-detect by hostname or IP
    hostname = socket.gethostname().lower()
    for node in MESH:
        if node.name in hostname:
            return node

    # Fallback: check if any mesh IP is bound locally
    try:
        import subprocess
        result = subprocess.run(
            ["ip", "-4", "addr", "show", "wg0"],
            capture_output=True, text=True, timeout=5,
        )
        for node in MESH:
            if node.ip in result.stdout:
                return node
    except Exception:
        pass

    # Default to central
    return MESH[0]


def peers(exclude_self: bool = True) -> list[Node]:
    """Get list of peer nodes (excluding self by default)."""
    me = whoami()
    if exclude_self:
        return [n for n in MESH if n.name != me.name]
    return list(MESH)


def repair_target() -> Node:
    """Who am I responsible for repairing?"""
    me = whoami()
    target_name = REPAIR_RING[me.name]
    return next(n for n in MESH if n.name == target_name)
