"""P4: Code generation from structured intent via Jinja2 templates.

Template design inspired by Arch Linux PKGBUILD:
  - Declarative: templates describe WHAT, not HOW
  - Idempotent: pre_check skips if already done
  - Verifiable: post_verify confirms success
  - Three phases: prepare → build → check

Each skill has a .sh.j2 template that generates a complete bash script
with pre-check (skip if already done), execute, and post-verify phases.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

# Skill → template file mapping
SKILL_TEMPLATES = {
    "install_package": "install_package.sh.j2",
    "edit_file": "edit_file.sh.j2",
    "restart_service": "restart_service.sh.j2",
    "run_command": "run_command.sh.j2",
    "check_status": "check_status.sh.j2",
}

# Auto-detect package manager from target hints
def _detect_manager(target: str, params: dict) -> str:
    """Detect package manager from context (Arch-style smart defaults)."""
    if "manager" in params:
        return params["manager"]
    # pip packages
    pip_hints = {"pandas", "numpy", "flask", "django", "requests", "httpx", "smolagents",
                 "instructor", "rich", "jinja2", "redis", "psycopg2", "sqlalchemy"}
    if target.lower() in pip_hints or params.get("pip"):
        return "pip"
    # npm packages
    npm_hints = {"express", "react", "vue", "typescript", "eslint", "prettier",
                 "openclaw", "clawhub", "antfarm"}
    if target.lower() in npm_hints or params.get("npm"):
        return "npm"
    return "apt"


def generate_command(skill: str, params: dict) -> str:
    """Generate a shell script from skill type and parameters using Jinja2 templates.

    Returns a complete bash script with pre-check, execute, and post-verify.
    """
    template_name = SKILL_TEMPLATES.get(skill)
    if not template_name:
        # Unknown skill: raw command fallback
        return params.get("target", "echo 'unknown skill'")

    template = _env.get_template(template_name)

    # Build context
    ctx = dict(params)

    # Auto-detect package manager for install
    if skill == "install_package":
        ctx["manager"] = _detect_manager(ctx.get("target", ""), ctx)

    return template.render(**ctx)


def generate_rollback(skill: str, params: dict) -> str | None:
    """Generate rollback command if possible.

    Arch-style: edit_file rolls back via .a2alaw-bak backup,
    install rolls back via remove.
    """
    target = params.get("target", "")
    manager = _detect_manager(target, params) if skill == "install_package" else "apt"

    rollback_map = {
        "install_package": {
            "apt": f"apt-get remove -y {target}",
            "pip": f"pip3 uninstall -y {target}",
            "npm": f"npm uninstall -g {target}",
            "pacman": f"pacman -R --noconfirm {target}",
            "dnf": f"dnf remove -y {target}",
        },
        "edit_file": f'[ -f "{target}.a2alaw-bak" ] && mv "{target}.a2alaw-bak" "{target}"',
        "restart_service": f"systemctl restart {target}",
    }

    rollback = rollback_map.get(skill)
    if isinstance(rollback, dict):
        return rollback.get(manager, f"apt-get remove -y {target}")
    if isinstance(rollback, str):
        return rollback
    return None
