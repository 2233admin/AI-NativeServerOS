"""OPA policy enforcement client for A2Alaw pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass

OPA_URL = os.environ.get("OPA_URL", "http://127.0.0.1:8181")
POLICY_PATH = "v1/data/a2alaw/safety"


@dataclass
class PolicyDecision:
    allowed: bool
    denied: bool
    deny_reasons: list[str]

    @property
    def blocked(self) -> bool:
        return self.denied or not self.allowed


def evaluate(
    action: str,
    target: str,
    command: str,
    risk_level: str,
    confidence: float,
    human_approved: bool = False,
) -> PolicyDecision:
    """Evaluate an action against OPA policies.

    Falls back to local evaluation if OPA is unreachable.
    """
    try:
        import httpx
        resp = httpx.post(
            f"{OPA_URL}/{POLICY_PATH}",
            json={
                "input": {
                    "action": action,
                    "target": target,
                    "command": command,
                    "risk_level": risk_level,
                    "confidence": confidence,
                    "human_approved": human_approved,
                }
            },
            timeout=3.0,
        )
        resp.raise_for_status()
        result = resp.json().get("result", {})
        return PolicyDecision(
            allowed=result.get("allow", False),
            denied=bool(result.get("deny", [])),
            deny_reasons=result.get("deny", []),
        )
    except Exception:
        return _local_evaluate(action, target, command, risk_level, confidence, human_approved)


def _local_evaluate(
    action: str,
    target: str,
    command: str,
    risk_level: str,
    confidence: float,
    human_approved: bool,
) -> PolicyDecision:
    """Fallback: evaluate locally when OPA is unreachable."""
    deny_reasons = []

    # Blacklist check
    blacklist = ["rm -rf /", "chmod 777", "> /dev/sd", "mkfs.", "dd if=", ":(){:|:&};:"]
    for pattern in blacklist:
        if pattern in command:
            deny_reasons.append(f"Blocked pattern: {pattern}")

    # Risk check
    if risk_level == "critical":
        deny_reasons.append(f"Critical risk action '{action}' on '{target}' requires human approval")
    if risk_level == "high" and not human_approved:
        deny_reasons.append(f"High risk action '{action}' requires approval")

    # Allow check
    allowed = False
    if risk_level == "low" and confidence >= 0.5:
        allowed = True
    elif risk_level == "medium" and confidence >= 0.7:
        allowed = True
    elif human_approved:
        allowed = True

    return PolicyDecision(
        allowed=allowed and not deny_reasons,
        denied=bool(deny_reasons),
        deny_reasons=deny_reasons,
    )
