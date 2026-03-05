"""P4: Code generation from structured intent via Jinja2 templates + LLM fallback."""

from __future__ import annotations

from string import Template

# Simple templates for Phase 1 MVP (Jinja2 in Phase 2)
TEMPLATES: dict[str, str] = {
    "install_package": "apt-get update -qq && apt-get install -y -qq $target",
    "restart_service": "systemctl restart $target",
    "check_status": "systemctl is-active $target 2>/dev/null || dpkg -l $target 2>/dev/null || echo 'unknown: $target'",
    "run_command": "$target",
    "edit_file": 'echo "$content" > $target',
}


def generate_command(skill: str, params: dict) -> str:
    """Generate a shell command from skill type and parameters.

    Phase 1: Template-based generation.
    Phase 2+: LLM-assisted generation for complex cases.
    """
    template_str = TEMPLATES.get(skill)
    if not template_str:
        raise ValueError(f"Unknown skill: {skill}")

    return Template(template_str).safe_substitute(params)


def generate_rollback(skill: str, params: dict) -> str | None:
    """Generate rollback command if possible."""
    rollback_map = {
        "install_package": Template("apt-get remove -y $target"),
        "restart_service": Template("systemctl restart $target"),
    }
    tmpl = rollback_map.get(skill)
    if tmpl:
        return tmpl.safe_substitute(params)
    return None
