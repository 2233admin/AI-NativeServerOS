#!/bin/bash
# A2Alaw atomic update via symlink switching
set -euo pipefail

RUNTIME_DIR="/var/lib/a2alaw/runtime"
SLOT_A="$RUNTIME_DIR/slot-a"
SLOT_B="$RUNTIME_DIR/slot-b"
CURRENT="$RUNTIME_DIR/current"
HEALTH_URL="http://127.0.0.1:8080/health"
ROLLBACK_TIMEOUT=30

# Determine inactive slot
if [ "$(readlink -f "$CURRENT")" = "$SLOT_A" ]; then
    TARGET="$SLOT_B"
    LABEL="slot-b"
else
    TARGET="$SLOT_A"
    LABEL="slot-a"
fi

echo "[update] Deploying to $LABEL..."

# Copy new version to target slot
rsync -a --delete "$1/" "$TARGET/"

# Atomic symlink switch
ln -sfn "$TARGET" "${CURRENT}.new"
mv -Tf "${CURRENT}.new" "$CURRENT"

echo "[update] Switched to $LABEL. Running health check..."

# Health check with rollback
sleep 2
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "[update] Health check passed."
else
    echo "[update] Health check FAILED! Rolling back in ${ROLLBACK_TIMEOUT}s..."
    exec "$(dirname "$0")/rollback.sh"
fi
