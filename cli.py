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
        print("  run <text>       Execute a natural language command (dry-run by default)")
        print("  run! <text>      Execute for real (sandbox)")
        print("  interactive      Start Rich TUI dialog")
        print("  init-streams     Initialize Redis Streams")
        print("  test             Run atomic loop test")
        return

    cmd = args[0]

    if cmd == "test":
        from a2alaw.test_loop import test_atomic_loop
        test_atomic_loop()

    elif cmd in ("run", "run!"):
        dry_run = cmd == "run"
        text = " ".join(args[1:]) if len(args) > 1 else sys.stdin.readline().strip()
        if not text:
            print("Error: no input provided", file=sys.stderr)
            sys.exit(1)

        from a2alaw.pipeline import Pipeline
        pipe = Pipeline(dry_run=dry_run)
        result = pipe.run(text)

        print(result.report)
        if result.audit_sha:
            print(f"Audit: {result.audit_sha}")
        print(f"Time: {result.total_ms}ms | Approved: {result.approved} | Success: {result.success}")

        if not result.success:
            sys.exit(1)

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


if __name__ == "__main__":
    main()
