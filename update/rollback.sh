#!/bin/bash
# A2Alaw rollback: switch back to previous slot
set -euo pipefail

RUNTIME_DIR="/var/lib/a2alaw/runtime"
SLOT_A="$RUNTIME_DIR/slot-a"
SLOT_B="$RUNTIME_DIR/slot-b"
CURRENT="$RUNTIME_DIR/current"

# Switch to the other slot
if [ "$(readlink -f "$CURRENT")" = "$SLOT_A" ]; then
    TARGET="$SLOT_B"
    LABEL="slot-b"
else
    TARGET="$SLOT_A"
    LABEL="slot-a"
fi

echo "[rollback] Switching back to $LABEL..."
ln -sfn "$TARGET" "${CURRENT}.new"
mv -Tf "${CURRENT}.new" "$CURRENT"
echo "[rollback] Done. Active: $LABEL"
