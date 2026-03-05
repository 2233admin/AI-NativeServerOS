#!/bin/bash
# OpenClaw One-Click Rollback
# Switches back to the previous slot instantly.
#
# Usage: sudo bash openclaw-rollback.sh

set -euo pipefail

OPENCLAW_DIR="/usr/lib/openclaw"
HEALTH_URL="http://127.0.0.1:18789/"

echo "=== OpenClaw Rollback ==="

CURRENT_SLOT="$(readlink /usr/lib/openclaw/core)"
if [ "$CURRENT_SLOT" = "slot-a" ]; then
    ROLLBACK_SLOT="slot-b"
else
    ROLLBACK_SLOT="slot-a"
fi

# Verify rollback slot exists
if [ ! -d "$OPENCLAW_DIR/$ROLLBACK_SLOT" ] || [ -z "$(ls -A "$OPENCLAW_DIR/$ROLLBACK_SLOT" 2>/dev/null)" ]; then
    echo "ERROR: $ROLLBACK_SLOT is empty. No previous version to roll back to."
    exit 1
fi

echo "Rolling back: $CURRENT_SLOT → $ROLLBACK_SLOT"

# Atomic switch
ln -sfn "$ROLLBACK_SLOT" "$OPENCLAW_DIR/core"
systemctl restart openclaw
sleep 3

# Verify
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "Rollback successful. Gateway running from $ROLLBACK_SLOT."
else
    echo "WARNING: Gateway not responding after rollback. Check: systemctl status openclaw"
fi
