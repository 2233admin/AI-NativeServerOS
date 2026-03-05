"""P1: Natural Language -> Structured Intent.

Three-tier LLM routing (cost-optimized):
  Tier 1: doubao-seed-2.0-code (free/cheap, Volcengine)
  Tier 2: claude-sonnet-4-6 (via yunyi proxy)
  Tier 3: minimax-M2.5 (fallback)

Falls back to rule-based parsing if all LLM tiers fail.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Three-tier LLM provider config (loaded from env or defaults)
LLM_PROVIDERS = [
    {
        "name": "doubao",
        "base_url": os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding"),
        "api_key": os.environ.get("DOUBAO_API_KEY", ""),
        "model": "doubao-seed-2.0-code",
        "api": "anthropic",  # anthropic messages format
    },
    {
        "name": "yunyi-claude",
        "base_url": os.environ.get("YUNYI_BASE_URL", ""),
        "api_key": os.environ.get("YUNYI_API_KEY", ""),
        "model": "claude-sonnet-4-6",
        "api": "anthropic",
    },
    {
        "name": "minimax",
        "base_url": os.environ.get("MINIMAX_BASE_URL", ""),
        "api_key": os.environ.get("MINIMAX_API_KEY", ""),
        "model": "MiniMax-M2.5",
        "api": "anthropic",
    },
]

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
    """Try each LLM provider in tier order until one succeeds."""
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx not installed")

    last_error = None
    for provider in LLM_PROVIDERS:
        if not provider["api_key"]:
            continue
        try:
            content = _call_anthropic_api(httpx, provider, nl_input)
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(content)
            return _build_intent(nl_input, parsed)
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("No LLM providers configured")


def _call_anthropic_api(httpx, provider: dict, nl_input: str) -> str:
    """Call an Anthropic Messages API compatible endpoint."""
    resp = httpx.post(
        f"{provider['base_url']}/v1/messages",
        headers={
            "x-api-key": provider["api_key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": provider["model"],
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": nl_input}],
            "temperature": 0,
            "max_tokens": 200,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"].strip()


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
