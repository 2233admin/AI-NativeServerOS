"""Restart service skill."""

SKILL_META = {
    "name": "restart_service",
    "version": "0.1.0",
    "action": "restart_service",
    "risk": "medium",
    "description": "Restart a systemd service",
}


def generate(target: str, **kwargs) -> str:
    return f"systemctl restart {target}"


def rollback(target: str, **kwargs) -> str:
    return f"systemctl restart {target}"
