#!/bin/bash
# ClawDebian Skill Package Manager
# Install, upgrade, remove, and list OpenClaw skills with full isolation.
#
# Usage:
#   claw-skill install <name> [tarball-url]
#   claw-skill upgrade <name> [tarball-url]
#   claw-skill remove <name>
#   claw-skill list

set -euo pipefail

ACTION="${1:-}"
SKILL_NAME="${2:-}"
SKILL_SOURCE="${3:-}"
SKILL_BASE="/var/lib/openclaw/skills"
LOG_BASE="/var/log/openclaw/skills"
SPAWN_SCRIPT="$(dirname "$0")/spawn-skill.sh"

case "$ACTION" in
    install)
        [ -z "$SKILL_NAME" ] && { echo "Usage: claw-skill install <name> [tarball-url]"; exit 1; }

        SKILL_DIR="$SKILL_BASE/$SKILL_NAME"
        if [ -d "$SKILL_DIR" ]; then
            echo "Skill $SKILL_NAME already installed. Use 'upgrade' instead."
            exit 1
        fi

        echo "Installing skill: $SKILL_NAME"
        mkdir -p "$SKILL_DIR"

        if [ -n "$SKILL_SOURCE" ]; then
            # Install from tarball URL
            echo "Downloading from: $SKILL_SOURCE"
            curl -fsSL "$SKILL_SOURCE" | tar -xz -C "$SKILL_DIR" --strip-components=1
        else
            # Create minimal skill skeleton
            echo "Creating skeleton for $SKILL_NAME"
            cat > "$SKILL_DIR/manifest.json" <<EOF
{
    "name": "$SKILL_NAME",
    "version": "0.1.0",
    "description": "OpenClaw skill: $SKILL_NAME",
    "entry": "index.js"
}
EOF
            cat > "$SKILL_DIR/index.js" <<'EOF'
// Skill entry point — implement your logic here
console.log(`Skill ${process.env.SKILL_ID} started`);
process.stdin.resume(); // Keep alive
EOF
        fi

        # Set permissions
        chown -R openclaw:openclaw "$SKILL_DIR" 2>/dev/null || true
        echo "Installed to: $SKILL_DIR"

        # Auto-start if spawn-skill.sh available
        if [ -x "$SPAWN_SCRIPT" ]; then
            bash "$SPAWN_SCRIPT" start "$SKILL_NAME" || true
        fi
        ;;

    upgrade)
        [ -z "$SKILL_NAME" ] && { echo "Usage: claw-skill upgrade <name> [tarball-url]"; exit 1; }

        SKILL_DIR="$SKILL_BASE/$SKILL_NAME"
        if [ ! -d "$SKILL_DIR" ]; then
            echo "Skill $SKILL_NAME not installed. Use 'install' first."
            exit 1
        fi

        echo "Upgrading skill: $SKILL_NAME"

        # Stop current
        bash "$SPAWN_SCRIPT" stop "$SKILL_NAME" 2>/dev/null || true

        # Backup old
        mv "$SKILL_DIR" "${SKILL_DIR}.old"

        # Install new
        mkdir -p "$SKILL_DIR"
        if [ -n "$SKILL_SOURCE" ]; then
            curl -fsSL "$SKILL_SOURCE" | tar -xz -C "$SKILL_DIR" --strip-components=1
        else
            echo "ERROR: No source URL for upgrade"
            mv "${SKILL_DIR}.old" "$SKILL_DIR"
            exit 1
        fi

        chown -R openclaw:openclaw "$SKILL_DIR" 2>/dev/null || true

        # Start new
        bash "$SPAWN_SCRIPT" start "$SKILL_NAME"

        # Verify (5s grace)
        sleep 5
        if systemctl is-active "openclaw-skill-${SKILL_NAME}" &>/dev/null; then
            rm -rf "${SKILL_DIR}.old"
            echo "Upgrade complete."
        else
            echo "New version failed — rolling back"
            rm -rf "$SKILL_DIR"
            mv "${SKILL_DIR}.old" "$SKILL_DIR"
            bash "$SPAWN_SCRIPT" start "$SKILL_NAME"
            echo "Rolled back to previous version."
            exit 1
        fi
        ;;

    remove)
        [ -z "$SKILL_NAME" ] && { echo "Usage: claw-skill remove <name>"; exit 1; }

        echo "Removing skill: $SKILL_NAME"

        # Stop process
        bash "$SPAWN_SCRIPT" stop "$SKILL_NAME" 2>/dev/null || true

        # Remove files
        rm -rf "$SKILL_BASE/$SKILL_NAME"

        # Archive log
        if [ -f "$LOG_BASE/${SKILL_NAME}.log" ]; then
            mv "$LOG_BASE/${SKILL_NAME}.log" "$LOG_BASE/${SKILL_NAME}.log.removed"
        fi

        echo "Removed: $SKILL_NAME"
        ;;

    list)
        echo "Installed skills:"
        if [ -d "$SKILL_BASE" ] && [ "$(ls -A "$SKILL_BASE" 2>/dev/null)" ]; then
            for dir in "$SKILL_BASE"/*/; do
                name="$(basename "$dir")"
                version="unknown"
                if [ -f "$dir/manifest.json" ]; then
                    version=$(python3 -c "import json; print(json.load(open('$dir/manifest.json')).get('version','?'))" 2>/dev/null || echo "?")
                fi
                status="stopped"
                systemctl is-active "openclaw-skill-${name}" &>/dev/null && status="running"
                printf "  %-25s v%-10s %s\n" "$name" "$version" "$status"
            done
        else
            echo "  (none)"
        fi
        ;;

    *)
        echo "ClawDebian Skill Manager"
        echo ""
        echo "Usage: claw-skill <command> [args]"
        echo ""
        echo "Commands:"
        echo "  install <name> [url]   Install a skill (from tarball or skeleton)"
        echo "  upgrade <name> <url>   Hot-upgrade a skill with rollback"
        echo "  remove <name>          Stop and remove a skill"
        echo "  list                   List installed skills"
        exit 1
        ;;
esac
