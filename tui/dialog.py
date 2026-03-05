"""Rich TUI for A2Alaw interactive dialog."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


def show_plan(dag: dict, risk_score: float) -> None:
    """Display execution plan for user review."""
    table = Table(title="Execution Plan")
    table.add_column("Step", style="cyan")
    table.add_column("Skill", style="green")
    table.add_column("Target")
    table.add_column("Risk", style="red")

    for i, node in enumerate(dag.get("nodes", []), 1):
        table.add_row(
            str(i),
            node["skill"],
            node["params"].get("target", ""),
            node["risk_level"],
        )

    console.print(table)
    console.print(f"\n[bold]Overall risk score:[/bold] {risk_score:.1%}")


def ask_approval(action: str, target: str, risk: str) -> bool:
    """Ask user for approval on risky actions."""
    console.print(
        Panel(
            f"[bold yellow]Action:[/bold yellow] {action}\n"
            f"[bold]Target:[/bold] {target}\n"
            f"[bold red]Risk:[/bold red] {risk}",
            title="Approval Required",
        )
    )
    return Confirm.ask("Proceed?")


def show_result(report: str, commit_sha: str | None = None) -> None:
    """Display execution result."""
    console.print(Panel(report, title="Result", border_style="green"))
    if commit_sha:
        console.print(f"[dim]Audit commit: {commit_sha}[/dim]")


def interactive_loop() -> None:
    """Main interactive TUI loop."""
    from a2alaw.orchestrator.dag_parser import parse_intent_to_dag
    from a2alaw.orchestrator.risk_scorer import requires_approval as check_approval

    console.print("[bold blue]A2Alaw[/bold blue] - Natural Language System Control")
    console.print("Type your command in natural language. 'quit' to exit.\n")

    while True:
        nl_input = Prompt.ask("[bold green]a2alaw[/bold green]")
        if nl_input.lower() in ("quit", "exit", "q"):
            break

        # Stub: In Phase 2, this goes through NL->Intent via smolagents
        intent = {
            "id": str(uuid.uuid4()),
            "nl_input": nl_input,
            "intent": {
                "action": "run",
                "target": nl_input,
            },
            "confidence": 0.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        dag = parse_intent_to_dag(intent)
        show_plan(dag.to_dict(), dag.risk_score)

        if check_approval(dag.risk_score, intent["confidence"]):
            if not ask_approval(nl_input, nl_input, f"{dag.risk_score:.0%}"):
                console.print("[yellow]Cancelled.[/yellow]")
                continue

        console.print("[dim]Execution would happen here (Phase 2)...[/dim]\n")
