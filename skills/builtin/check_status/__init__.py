"""Check status skill."""

SKILL_META = {
    "name": "check_status",
    "version": "0.1.0",
    "action": "check_status",
    "risk": "low",
    "description": "Check status of a service or package",
}


def generate(target: str, **kwargs) -> str:
    return f"systemctl is-active {target} 2>/dev/null || dpkg -l {target} 2>/dev/null || echo 'unknown: {target}'"


def rollback(target: str, **kwargs) -> str | None:
    return None  # Read-only
