"""Install package skill."""

SKILL_META = {
    "name": "install_package",
    "version": "0.1.0",
    "action": "install_package",
    "risk": "low",
    "description": "Install a system package via apt",
}


def generate(target: str, **kwargs) -> str:
    return f"apt-get update -qq && apt-get install -y -qq {target}"


def rollback(target: str, **kwargs) -> str:
    return f"apt-get remove -y {target}"
