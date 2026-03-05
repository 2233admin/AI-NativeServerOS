"""P2: Intent -> Execution DAG via LLM."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SkillType(str, Enum):
    INSTALL_PACKAGE = "install_package"
    EDIT_FILE = "edit_file"
    RESTART_SERVICE = "restart_service"
    RUN_COMMAND = "run_command"
    CHECK_STATUS = "check_status"


@dataclass
class DAGNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    skill: SkillType = SkillType.RUN_COMMAND
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    risk_level: str = "low"


@dataclass
class ExecutionDAG:
    intent_id: str
    nodes: list[DAGNode] = field(default_factory=list)
    risk_score: float = 0.0

    def topological_order(self) -> list[DAGNode]:
        """Return nodes in dependency-respecting execution order."""
        visited: set[str] = set()
        result: list[DAGNode] = []
        node_map = {n.id: n for n in self.nodes}

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            node = node_map[node_id]
            for dep in node.depends_on:
                visit(dep)
            result.append(node)

        for n in self.nodes:
            visit(n.id)
        return result

    def to_dict(self) -> dict:
        return {
            "intent_id": self.intent_id,
            "nodes": [
                {
                    "id": n.id,
                    "skill": n.skill.value,
                    "params": n.params,
                    "depends_on": n.depends_on,
                    "risk_level": n.risk_level,
                }
                for n in self.nodes
            ],
            "risk_score": self.risk_score,
        }


def parse_intent_to_dag(intent: dict) -> ExecutionDAG:
    """Convert a structured intent into an execution DAG.

    For Phase 1 MVP, this uses simple rule-based mapping.
    Phase 2+ will use smolagents/LLM for complex multi-step intents.
    """
    action = intent["intent"]["action"]
    target = intent["intent"]["target"]
    params = intent["intent"].get("params", {})

    dag = ExecutionDAG(intent_id=intent["id"])

    skill_map = {
        "install": SkillType.INSTALL_PACKAGE,
        "edit": SkillType.EDIT_FILE,
        "restart": SkillType.RESTART_SERVICE,
        "run": SkillType.RUN_COMMAND,
        "check": SkillType.CHECK_STATUS,
    }

    # Pre-check node
    check_node = DAGNode(
        skill=SkillType.CHECK_STATUS,
        params={"target": target},
        risk_level="low",
    )
    dag.nodes.append(check_node)

    # Main action node
    main_node = DAGNode(
        skill=skill_map.get(action, SkillType.RUN_COMMAND),
        params={"target": target, **params},
        depends_on=[check_node.id],
        risk_level=_assess_risk(action, target),
    )
    dag.nodes.append(main_node)

    dag.risk_score = max(
        {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 1.0}[n.risk_level]
        for n in dag.nodes
    )

    return dag


def _assess_risk(action: str, target: str) -> str:
    high_risk_targets = {"sshd", "firewall", "ufw", "iptables", "systemd", "kernel"}
    if any(t in target.lower() for t in high_risk_targets):
        return "critical"
    if action in ("restart", "edit"):
        return "medium"
    if action == "install":
        return "low"
    return "medium"
