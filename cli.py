"""A2Alaw CLI entry point.

Usage:
  echo "安装 pandas" | python -m a2alaw.cli run
  python -m a2alaw.cli run "重启 nginx"
  python -m a2alaw.cli interactive
  python -m a2alaw.cli init-streams
"""

from __future__ import annotations

import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: a2alawctl <command> [args]")
        print()
        print("Commands:")
        print("  run <text>       Preview a command (dry-run)")
        print("  run! <text>      Execute on host (real system changes)")
        print("  agent <text>     Multi-step planning via smolagents (dry-run)")
        print("  agent! <text>    Multi-step planning + host execution")
        print("  interactive      Start Rich TUI dialog")
        print("  init-streams     Initialize Redis Streams")
        print("  test             Run atomic loop test")
        return

    cmd = args[0]

    if cmd == "test":
        from a2alaw.test_loop import test_atomic_loop
        test_atomic_loop()

    elif cmd in ("run", "run!", "agent", "agent!"):
        dry_run = cmd in ("run", "agent")
        use_agent = cmd.startswith("agent")
        text = " ".join(args[1:]) if len(args) > 1 else sys.stdin.readline().strip()
        if not text:
            print("Error: no input provided", file=sys.stderr)
            sys.exit(1)

        from a2alaw.pipeline import Pipeline

        event_bus = _try_connect_streams()
        pipe = Pipeline(dry_run=dry_run, event_bus=event_bus, use_agent=use_agent)
        result = pipe.run(text)

        print(result.report)
        if result.policy_blocked:
            print(f"Policy: {'; '.join(result.policy_reasons)}")
        if result.audit_sha:
            print(f"Audit: {result.audit_sha}")
        streams = "connected" if event_bus else "offline"
        print(f"Time: {result.total_ms}ms | Approved: {result.approved} | Success: {result.success} | Streams: {streams}")

        if not result.success and not result.policy_blocked:
            sys.exit(1)
        if result.policy_blocked:
            sys.exit(2)

    elif cmd == "interactive":
        from a2alaw.tui.dialog import interactive_loop
        interactive_loop()

    elif cmd == "init-streams":
        from a2alaw.feedback.redis_streams import EventBus
        bus = EventBus()
        bus.init_streams()
        print("Redis Streams initialized.")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


def _try_connect_streams():
    """Try to connect to Redis Streams event bus."""
    try:
        from a2alaw.feedback.redis_streams import EventBus
        bus = EventBus()
        bus.r.ping()
        return bus
    except Exception:
        return None


if __name__ == "__main__":
    main()
