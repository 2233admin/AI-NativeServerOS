"""Run command skill."""

SKILL_META = {
    "name": "run_command",
    "version": "0.1.0",
    "action": "run_command",
    "risk": "medium",
    "description": "Execute an arbitrary shell command",
}


def generate(target: str, **kwargs) -> str:
    return target


def rollback(target: str, **kwargs) -> str | None:
    return None
