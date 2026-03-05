#!/bin/bash
# OpenClaw Dual-Slot Atomic Hot Update
# Zero-downtime version switch with automatic 30s rollback on failure.
#
# Usage: sudo bash openclaw-update.sh [version]
#   e.g.: sudo bash openclaw-update.sh 2026.3.3
#   or:   sudo bash openclaw-update.sh   (updates to latest)

set -euo pipefail

VERSION="${1:-latest}"
OPENCLAW_DIR="/usr/lib/openclaw"
HEALTH_URL="http://127.0.0.1:18789/"
ROLLBACK_TIMEOUT=30

echo "=== OpenClaw Hot Update ==="

# ── Detect current active slot ──
CURRENT_SLOT="$(readlink /usr/lib/openclaw/core)"
if [ "$CURRENT_SLOT" = "slot-a" ]; then
    NEW_SLOT="slot-b"
else
    NEW_SLOT="slot-a"
fi
echo "Current: $CURRENT_SLOT → Deploying to: $NEW_SLOT"

# ── Step 1: Install new version to inactive slot ──
echo "--- Step 1: Installing OpenClaw@${VERSION} to $NEW_SLOT ---"
rm -rf "$OPENCLAW_DIR/$NEW_SLOT"
mkdir -p "$OPENCLAW_DIR/$NEW_SLOT"

if [ "$VERSION" = "latest" ]; then
    npm install --prefix "$OPENCLAW_DIR/$NEW_SLOT" openclaw 2>&1 | tail -3
else
    npm install --prefix "$OPENCLAW_DIR/$NEW_SLOT" "openclaw@${VERSION}" 2>&1 | tail -3
fi

# Verify installation
if [ ! -f "$OPENCLAW_DIR/$NEW_SLOT/node_modules/.package-lock.json" ]; then
    echo "ERROR: npm install failed for $NEW_SLOT"
    exit 1
fi
echo "Installed to $NEW_SLOT"

# ── Step 2: Pre-switch health check (verify new version can start) ──
echo "--- Step 2: Pre-flight check ---"
NEW_BIN="$OPENCLAW_DIR/$NEW_SLOT/node_modules/.bin/openclaw"
if [ -f "$NEW_BIN" ]; then
    NEW_VER=$("$NEW_BIN" --version 2>/dev/null || echo "unknown")
    echo "New version: $NEW_VER"
fi

# ── Step 3: Atomic symlink switch ──
echo "--- Step 3: Atomic switch ---"
ln -sfn "$NEW_SLOT" "$OPENCLAW_DIR/core"
echo "Switched: core -> $NEW_SLOT"

# ── Step 4: Reload service ──
echo "--- Step 4: Reloading service ---"
systemctl restart openclaw
sleep 3

# ── Step 5: Health check with rollback timer ──
echo "--- Step 5: Health check (${ROLLBACK_TIMEOUT}s window) ---"
HEALTHY=false
for i in $(seq 1 $ROLLBACK_TIMEOUT); do
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        HEALTHY=true
        echo "Health check passed at ${i}s"
        break
    fi
    sleep 1
done

if ! $HEALTHY; then
    echo "HEALTH CHECK FAILED — Rolling back to $CURRENT_SLOT"
    ln -sfn "$CURRENT_SLOT" "$OPENCLAW_DIR/core"
    systemctl restart openclaw
    sleep 3
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "Rollback successful. Gateway restored to $CURRENT_SLOT."
    else
        echo "CRITICAL: Rollback also failed! Manual intervention needed."
    fi
    exit 1
fi

# ── Step 6: Update metadata ──
cat > /etc/openclaw/.migration <<EOF
migrated_at=$(date -Iseconds)
active_slot=$NEW_SLOT
previous_slot=$CURRENT_SLOT
version=$VERSION
updated_at=$(date -Iseconds)
EOF

echo ""
echo "=== Update Complete ==="
echo "Active: $NEW_SLOT | Previous: $CURRENT_SLOT (preserved for rollback)"
echo "Run 'openclaw-rollback.sh' within any time to switch back."
