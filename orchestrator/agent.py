"""Multi-step orchestrator powered by smolagents CodeAgent.

Converts complex NL requests into compound DAGs by letting the agent
plan and sequence multiple atomic skills.

Uses LiteLLM for provider flexibility (Doubao/Claude/MiniMax via FreeClaw routing).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from smolagents import Tool, CodeAgent, LiteLLMModel

from a2alaw.orchestrator.dag_parser import DAGNode, ExecutionDAG, SkillType
from a2alaw.orchestrator.nl_parser import ParsedIntent, _infer_risk


# ── Atomic Skill Tools for smolagents ──────────────────────────────

class InstallPackageTool(Tool):
    name = "install_package"
    description = "Install a system package. Returns the package name to install."
    inputs = {
        "package": {"type": "string", "description": "Package name to install (e.g. nginx, python3-pip)"}
    }
    output_type = "string"

    def forward(self, package: str) -> str:
        return json.dumps({"skill": "install_package", "target": package})


class EditFileTool(Tool):
    name = "edit_file"
    description = "Edit or create a file on the system. Returns the file path and content."
    inputs = {
        "path": {"type": "string", "description": "File path to edit"},
        "content": {"type": "string", "description": "New content for the file"},
    }
    output_type = "string"

    def forward(self, path: str, content: str) -> str:
        return json.dumps({"skill": "edit_file", "target": path, "params": {"content": content}})


class RestartServiceTool(Tool):
    name = "restart_service"
    description = "Restart a systemd service. Returns the service name."
    inputs = {
        "service": {"type": "string", "description": "Service name (e.g. nginx, redis, sshd)"}
    }
    output_type = "string"

    def forward(self, service: str) -> str:
        return json.dumps({"skill": "restart_service", "target": service})


class RunCommandTool(Tool):
    name = "run_command"
    description = "Execute a shell command. Returns the command string."
    inputs = {
        "command": {"type": "string", "description": "Shell command to execute"}
    }
    output_type = "string"

    def forward(self, command: str) -> str:
        return json.dumps({"skill": "run_command", "target": command})


class CheckStatusTool(Tool):
    name = "check_status"
    description = "Check status of a service or package. Returns the target to check."
    inputs = {
        "target": {"type": "string", "description": "Service or package name to check"}
    }
    output_type = "string"

    def forward(self, target: str) -> str:
        return json.dumps({"skill": "check_status", "target": target})


SKILL_TOOLS = [
    InstallPackageTool(),
    EditFileTool(),
    RestartServiceTool(),
    RunCommandTool(),
    CheckStatusTool(),
]

SKILL_MAP = {
    "install_package": SkillType.INSTALL_PACKAGE,
    "edit_file": SkillType.EDIT_FILE,
    "restart_service": SkillType.RESTART_SERVICE,
    "run_command": SkillType.RUN_COMMAND,
    "check_status": SkillType.CHECK_STATUS,
}

AGENT_SYSTEM_PROMPT = """You are A2Alaw, a system administration agent. You break down user requests into atomic operations.

IMPORTANT RULES:
1. Use ONLY the provided tools. Each tool call represents one atomic step.
2. For multi-step tasks, call tools in the correct dependency order.
3. Always check status before making changes when appropriate.
4. Return a summary of all planned steps at the end.

Example: "安装 nginx 并配置反向代理"
→ Step 1: install_package("nginx")
→ Step 2: edit_file("/etc/nginx/conf.d/proxy.conf", "server { ... }")
→ Step 3: restart_service("nginx")
→ Step 4: check_status("nginx")
"""


def _create_model() -> LiteLLMModel:
    """Create LiteLLM model for agent planning.

    Tries providers in order:
    1. yunyi-claude (Claude Sonnet, best tool-use support)
    2. Doubao (cheaper but less reliable for tool calling)
    """
    # Try Claude first (best at tool use / multi-step)
    yunyi_key = os.environ.get("YUNYI_API_KEY", "")
    yunyi_base = os.environ.get("YUNYI_BASE_URL", "")
    if yunyi_key and yunyi_base:
        return LiteLLMModel(
            model_id="anthropic/claude-sonnet-4-6",
            api_base=yunyi_base,
            api_key=yunyi_key,
            temperature=0,
            max_tokens=1000,
        )

    # Fallback to Doubao
    doubao_key = os.environ.get("DOUBAO_API_KEY", "")
    doubao_base = os.environ.get("DOUBAO_BASE_URL", "")
    if doubao_key:
        return LiteLLMModel(
            model_id="anthropic/doubao-seed-2.0-code",
            api_base=doubao_base,
            api_key=doubao_key,
            temperature=0,
            max_tokens=1000,
        )

    raise RuntimeError("No LLM API keys configured for agent mode")


def plan_multi_step(nl_input: str) -> tuple[ParsedIntent, ExecutionDAG]:
    """Use smolagents CodeAgent to decompose NL into a multi-step DAG.

    Returns (intent, dag) where dag may have multiple nodes.
    """
    model = _create_model()
    agent = CodeAgent(
        tools=SKILL_TOOLS,
        model=model,
        max_steps=8,
        verbosity_level=0,
    )

    # Run agent — it will call tools in sequence
    try:
        agent_result = agent.run(nl_input)
    except Exception as e:
        # Fallback to single-step
        from a2alaw.orchestrator.nl_parser import parse_nl
        from a2alaw.orchestrator.dag_parser import parse_intent_to_dag
        intent = parse_nl(nl_input)
        dag = parse_intent_to_dag(intent.to_dict())
        return intent, dag

    # Extract tool calls from agent's memory
    dag = ExecutionDAG(intent_id=str(uuid.uuid4()))
    steps = _extract_steps_from_memory(agent)

    if not steps:
        # Agent didn't call any tools, fall back
        from a2alaw.orchestrator.nl_parser import parse_nl
        from a2alaw.orchestrator.dag_parser import parse_intent_to_dag
        intent = parse_nl(nl_input)
        dag = parse_intent_to_dag(intent.to_dict())
        return intent, dag

    prev_id = None
    primary_action = "run"
    primary_target = nl_input

    for step in steps:
        skill_name = step.get("skill", "run_command")
        target = step.get("target", "")
        params = step.get("params", {})
        params["target"] = target

        node = DAGNode(
            skill=SKILL_MAP.get(skill_name, SkillType.RUN_COMMAND),
            params=params,
            depends_on=[prev_id] if prev_id else [],
            risk_level=_infer_risk(skill_name.replace("_", " ").split()[0], target),
        )
        dag.nodes.append(node)
        prev_id = node.id

        # Use first non-check action as primary
        if skill_name != "check_status" and primary_action == "run":
            primary_action = skill_name.split("_")[0] if "_" in skill_name else skill_name
            primary_target = target

    dag.risk_score = max(
        {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 1.0}.get(n.risk_level, 0.5)
        for n in dag.nodes
    ) if dag.nodes else 0.1

    intent = ParsedIntent(
        id=dag.intent_id,
        nl_input=nl_input,
        action=primary_action,
        target=primary_target,
        params={},
        confidence=0.9,
        risk_level=max(
            (n.risk_level for n in dag.nodes),
            key=lambda r: ["low", "medium", "high", "critical"].index(r),
        ) if dag.nodes else "low",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return intent, dag


def _extract_steps_from_memory(agent: CodeAgent) -> list[dict]:
    """Extract structured steps from agent's memory (smolagents 1.24+).

    Steps are dicts with 'observations' containing JSON tool outputs.
    """
    steps = []
    try:
        for mem_step in agent.memory.get_full_steps():
            if not isinstance(mem_step, dict) or "step_number" not in mem_step:
                continue
            observations = mem_step.get("observations", "")
            if not observations:
                continue
            # Parse JSON objects from observations
            # Agent may print results like "Install result: {json}" or just "{json}"
            import re
            for match in re.finditer(r'\{[^{}]+\}', observations):
                try:
                    parsed = json.loads(match.group())
                    if "skill" in parsed:
                        steps.append(parsed)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return steps
