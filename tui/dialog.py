"""Rich TUI for A2Alaw interactive dialog."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

console = Console()


def show_intent(intent) -> None:
    """Display parsed intent."""
    risk_colors = {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}
    color = risk_colors.get(intent.risk_level, "white")

    table = Table.grid(padding=(0, 2))
    table.add_row("Input:", intent.nl_input)
    table.add_row("Action:", f"[cyan]{intent.action}[/]")
    table.add_row("Target:", f"[bold]{intent.target}[/]")
    table.add_row("Confidence:", f"{intent.confidence:.0%}")
    table.add_row("Risk:", f"[{color}]{intent.risk_level}[/]")

    console.print(Panel(table, title="Intent", border_style="blue"))


def show_plan(dag, risk_score: float) -> None:
    """Display execution plan."""
    table = Table(title="Execution Plan", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Skill", style="cyan")
    table.add_column("Target")
    table.add_column("Risk")
    table.add_column("Depends", style="dim")

    risk_colors = {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}

    for i, node in enumerate(dag.get("nodes", []), 1):
        color = risk_colors.get(node["risk_level"], "white")
        deps = ", ".join(node["depends_on"][:8]) if node["depends_on"] else "-"
        table.add_row(
            str(i),
            node["skill"],
            node["params"].get("target", ""),
            f"[{color}]{node['risk_level']}[/]",
            deps,
        )

    console.print(table)
    console.print(f"Overall risk: [bold]{risk_score:.0%}[/]")


def show_result(result) -> None:
    """Display pipeline result."""
    if result.policy_blocked:
        console.print(Panel(
            "\n".join(f"[red]• {r}[/]" for r in result.policy_reasons),
            title="[bold red]BLOCKED BY POLICY[/]",
            border_style="red",
        ))
        return

    style = "green" if result.success else "red"
    console.print(Panel(result.report, title="Result", border_style=style))

    if result.audit_sha:
        console.print(f"  [dim]Audit commit: {result.audit_sha}[/]")
    console.print(f"  [dim]Time: {result.total_ms}ms[/]\n")


def ask_approval(action: str, target: str, risk: str) -> bool:
    """Ask user for approval on risky actions."""
    console.print(Panel(
        f"[bold yellow]Action:[/] {action}\n"
        f"[bold]Target:[/] {target}\n"
        f"[bold red]Risk:[/] {risk}",
        title="Approval Required",
        border_style="yellow",
    ))
    return Confirm.ask("[yellow]Proceed?[/]")


def interactive_loop() -> None:
    """Main interactive TUI loop."""
    from a2alaw.pipeline import Pipeline

    # Try connecting to streams
    event_bus = None
    try:
        from a2alaw.feedback.redis_streams import EventBus
        bus = EventBus()
        bus.r.ping()
        event_bus = bus
    except Exception:
        pass

    console.print()
    console.print(Panel(
        "[bold blue]A2Alaw[/] — Natural Language System Control\n"
        f"Streams: {'[green]connected[/]' if event_bus else '[dim]offline[/]'}",
        border_style="blue",
    ))
    console.print("[dim]Commands: type natural language, 'dry' prefix for dry-run, 'quit' to exit[/]\n")

    pipe_live = Pipeline(dry_run=False, event_bus=event_bus, approval_fn=ask_approval)
    pipe_dry = Pipeline(dry_run=True, event_bus=event_bus)

    while True:
        try:
            nl_input = Prompt.ask("[bold green]a2alaw[/]")
        except (KeyboardInterrupt, EOFError):
            break

        if nl_input.lower() in ("quit", "exit", "q"):
            break

        if not nl_input.strip():
            continue

        # dry prefix for dry-run
        if nl_input.startswith("dry "):
            pipe = pipe_dry
            nl_input = nl_input[4:]
        else:
            pipe = pipe_live

        result = pipe.run(nl_input)
        show_intent(result.intent)
        if not result.policy_blocked:
            show_plan(result.dag.to_dict(), result.dag.risk_score)
        show_result(result)

    console.print("[dim]Goodbye.[/]")
