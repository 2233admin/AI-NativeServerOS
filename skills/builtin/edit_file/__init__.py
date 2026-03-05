"""Edit file skill."""

SKILL_META = {
    "name": "edit_file",
    "version": "0.1.0",
    "action": "edit_file",
    "risk": "medium",
    "description": "Edit a file on the system",
}


def generate(target: str, content: str = "", **kwargs) -> str:
    return f'cat > {target} << "A2AEOF"\n{content}\nA2AEOF'


def rollback(target: str, **kwargs) -> str | None:
    return None  # Requires snapshot
