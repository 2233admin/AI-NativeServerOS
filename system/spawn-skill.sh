#!/bin/bash
# Spawn an OpenClaw skill as an isolated subprocess
# Each skill runs in its own cgroup with resource limits,
# independent node_modules, and separate logging.
#
# Usage: spawn-skill.sh <action> <skill-id> [skill-path]
#   spawn-skill.sh start nginx-skill
#   spawn-skill.sh stop nginx-skill
#   spawn-skill.sh restart nginx-skill
#   spawn-skill.sh status nginx-skill

set -euo pipefail

ACTION="${1:-}"
SKILL_ID="${2:-}"
SKILL_BASE="/var/lib/openclaw/skills"
LOG_BASE="/var/log/openclaw/skills"

if [ -z "$ACTION" ] || [ -z "$SKILL_ID" ]; then
    echo "Usage: spawn-skill.sh <start|stop|restart|status> <skill-id>"
    exit 1
fi

SKILL_DIR="$SKILL_BASE/$SKILL_ID"
SKILL_LOG="$LOG_BASE/${SKILL_ID}.log"
UNIT_NAME="openclaw-skill-${SKILL_ID}"

case "$ACTION" in
    start)
        if [ ! -d "$SKILL_DIR" ]; then
            echo "ERROR: Skill not found: $SKILL_DIR"
            exit 1
        fi
        if [ ! -f "$SKILL_DIR/index.js" ]; then
            echo "ERROR: No index.js in $SKILL_DIR"
            exit 1
        fi

        echo "Starting skill: $SKILL_ID"

        # Launch as isolated systemd transient unit
        systemd-run \
            --unit="$UNIT_NAME" \
            --description="OpenClaw Skill: $SKILL_ID" \
            --property=CPUQuota=10% \
            --property=MemoryMax=256M \
            --property=Restart=on-failure \
            --property=RestartSec=3 \
            --property="StandardOutput=append:$SKILL_LOG" \
            --property="StandardError=append:$SKILL_LOG" \
            --property="WorkingDirectory=$SKILL_DIR" \
            --property="Environment=SKILL_ID=$SKILL_ID" \
            --property="Environment=OPENCLAW_STATE_DIR=/var/lib/openclaw" \
            /usr/bin/node "$SKILL_DIR/index.js"

        echo "Started: $UNIT_NAME (log: $SKILL_LOG)"
        ;;

    stop)
        echo "Stopping skill: $SKILL_ID"
        systemctl stop "$UNIT_NAME" 2>/dev/null || true
        echo "Stopped: $UNIT_NAME"
        ;;

    restart)
        "$0" stop "$SKILL_ID"
        sleep 1
        "$0" start "$SKILL_ID"
        ;;

    status)
        systemctl status "$UNIT_NAME" --no-pager 2>/dev/null || echo "$UNIT_NAME: not running"
        if [ -f "$SKILL_LOG" ]; then
            echo "--- Last 5 log lines ---"
            tail -5 "$SKILL_LOG"
        fi
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid: start, stop, restart, status"
        exit 1
        ;;
esac
