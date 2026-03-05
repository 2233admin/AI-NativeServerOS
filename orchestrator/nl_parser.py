"""P1: Natural Language -> Structured Intent.

Uses OpenClaw FreeClaw three-tier routing:
  claude -> doubao -> minimax

Phase 1: instructor + structured output
Phase 2+: smolagents for multi-step reasoning
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# FreeClaw routing via OpenAI-compatible API
FREECLAW_BASE = os.environ.get("FREECLAW_BASE_URL", "http://127.0.0.1:18789/v1")
FREECLAW_KEY = os.environ.get("FREECLAW_API_KEY", "")

VALID_ACTIONS = {"install", "edit", "restart", "run", "check"}

SYSTEM_PROMPT = """You are A2Alaw's intent parser. Convert natural language system administration commands into structured JSON.

Output EXACTLY this JSON format (no markdown, no explanation):
{
  "action": "install|edit|restart|run|check",
  "target": "<package/service/file/command>",
  "params": {},
  "confidence": 0.0-1.0
}

Action mapping:
- install: installing packages (apt, pip, npm, etc.)
- edit: modifying files or configurations
- restart: restarting/starting/stopping services
- run: executing arbitrary commands
- check: checking status of services/packages/systems

Examples:
- "安装 pandas" -> {"action": "install", "target": "python3-pandas", "params": {}, "confidence": 0.95}
- "重启 nginx" -> {"action": "restart", "target": "nginx", "params": {}, "confidence": 0.98}
- "查看磁盘使用" -> {"action": "run", "target": "df -h", "params": {}, "confidence": 0.90}
- "把 /etc/hostname 改成 claw-central" -> {"action": "edit", "target": "/etc/hostname", "params": {"content": "claw-central"}, "confidence": 0.92}
"""


@dataclass
class ParsedIntent:
    id: str
    nl_input: str
    action: str
    target: str
    params: dict[str, Any]
    confidence: float
    risk_level: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nl_input": self.nl_input,
            "intent": {
                "action": self.action,
                "target": self.target,
                "params": self.params,
                "constraints": {"dry_run": False, "require_approval": True},
            },
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "timestamp": self.timestamp,
        }


def parse_nl(nl_input: str) -> ParsedIntent:
    """Parse natural language into structured intent.

    Tries LLM first, falls back to rule-based parsing.
    """
    try:
        return _parse_via_llm(nl_input)
    except Exception:
        return _parse_rule_based(nl_input)


def _parse_via_llm(nl_input: str) -> ParsedIntent:
    """Use FreeClaw LLM routing to parse intent."""
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx not installed")

    resp = httpx.post(
        f"{FREECLAW_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {FREECLAW_KEY}"},
        json={
            "model": "claude-proxy/claude-sonnet-4",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": nl_input},
            ],
            "temperature": 0,
            "max_tokens": 200,
        },
        timeout=15.0,
    )
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    parsed = json.loads(content)
    return _build_intent(nl_input, parsed)


def _parse_rule_based(nl_input: str) -> ParsedIntent:
    """Simple rule-based fallback parser for common patterns."""
    text = nl_input.strip().lower()

    # Chinese keyword mapping
    action_keywords = {
        "install": ["安装", "装一下", "install", "pip install", "apt install"],
        "restart": ["重启", "启动", "停止", "restart", "start", "stop"],
        "check": ["查看", "检查", "状态", "check", "status", "show"],
        "edit": ["修改", "编辑", "改成", "写入", "edit", "change"],
        "run": ["运行", "执行", "跑一下", "run", "exec"],
    }

    action = "run"
    for act, keywords in action_keywords.items():
        if any(kw in text for kw in keywords):
            action = act
            break

    # Extract target: everything after the action keyword
    target = nl_input.strip()
    for keywords in action_keywords.values():
        for kw in keywords:
            if kw in text:
                idx = text.find(kw)
                remainder = nl_input.strip()[idx + len(kw):].strip()
                if remainder:
                    target = remainder
                break

    risk = _infer_risk(action, target)

    return ParsedIntent(
        id=str(uuid.uuid4()),
        nl_input=nl_input,
        action=action,
        target=target,
        params={},
        confidence=0.6,  # Rule-based gets lower confidence
        risk_level=risk,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _build_intent(nl_input: str, parsed: dict) -> ParsedIntent:
    """Build ParsedIntent from LLM output."""
    action = parsed.get("action", "run")
    if action not in VALID_ACTIONS:
        action = "run"

    target = parsed.get("target", nl_input)
    confidence = min(max(float(parsed.get("confidence", 0.5)), 0.0), 1.0)
    risk = _infer_risk(action, target)

    return ParsedIntent(
        id=str(uuid.uuid4()),
        nl_input=nl_input,
        action=action,
        target=target,
        params=parsed.get("params", {}),
        confidence=confidence,
        risk_level=risk,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _infer_risk(action: str, target: str) -> str:
    critical_targets = {"sshd", "firewall", "ufw", "iptables", "kernel", "/etc/passwd", "/etc/shadow"}
    if any(t in target.lower() for t in critical_targets):
        return "critical"
    if action in ("restart", "edit"):
        return "medium"
    return "low"
