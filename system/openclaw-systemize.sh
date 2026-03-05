#!/bin/bash
# OpenClaw System-Level Migration
# Transforms OpenClaw from user-land npm package to system-level infrastructure.
# Non-invasive: uses OPENCLAW_HOME/CONFIG_PATH/STATE_DIR env vars, no source modification.
#
# Usage: sudo bash openclaw-systemize.sh
#
# Prerequisites: OpenClaw already installed via npm (to copy from)

set -euo pipefail

echo "=== OpenClaw System-Level Migration ==="

# ── Detect current installation ──
CURRENT_OPENCLAW=""
if [ -d /usr/lib/node_modules/openclaw ]; then
    CURRENT_OPENCLAW="/usr/lib/node_modules/openclaw"
elif [ -d /root/.openclaw ] && command -v openclaw &>/dev/null; then
    CURRENT_OPENCLAW="$(dirname "$(dirname "$(readlink -f "$(which openclaw)")")")"
fi

if [ -z "$CURRENT_OPENCLAW" ]; then
    echo "ERROR: No existing OpenClaw installation found."
    echo "Install first: npm i -g openclaw"
    exit 1
fi
echo "Found OpenClaw at: $CURRENT_OPENCLAW"

# ── Step 1: Create FHS directory structure ──
echo "--- Step 1: Creating system directories ---"
mkdir -p /usr/lib/openclaw/{slot-a,slot-b}
mkdir -p /etc/openclaw/skills.d
mkdir -p /var/lib/openclaw/{workspace,memory,devices,extensions,skills}
mkdir -p /var/log/openclaw/skills
mkdir -p /run/openclaw

# ── Step 2: Copy current installation to slot-a ──
echo "--- Step 2: Deploying to slot-a ---"
if [ ! -f /usr/lib/openclaw/slot-a/package.json ]; then
    cp -a "$CURRENT_OPENCLAW"/* /usr/lib/openclaw/slot-a/
    echo "Copied from $CURRENT_OPENCLAW"
else
    echo "slot-a already populated, skipping"
fi

# Create active version symlink
ln -sfn slot-a /usr/lib/openclaw/core
echo "Active: /usr/lib/openclaw/core -> slot-a"

# ── Step 3: Migrate configuration ──
echo "--- Step 3: Migrating configuration ---"
OLD_CONFIG_DIR="${HOME}/.openclaw"

if [ -f "$OLD_CONFIG_DIR/openclaw.json" ] && [ ! -f /etc/openclaw/openclaw.json ]; then
    cp -p "$OLD_CONFIG_DIR/openclaw.json" /etc/openclaw/
    echo "Migrated openclaw.json"
fi

# Migrate data directories (if not already done)
for dir in workspace memory devices; do
    if [ -d "$OLD_CONFIG_DIR/$dir" ] && [ "$(ls -A "$OLD_CONFIG_DIR/$dir" 2>/dev/null)" ]; then
        if [ ! "$(ls -A /var/lib/openclaw/$dir 2>/dev/null)" ]; then
            cp -a "$OLD_CONFIG_DIR/$dir"/* /var/lib/openclaw/$dir/ 2>/dev/null || true
            echo "Migrated $dir"
        fi
    fi
done

# Migrate extensions
if [ -d "$OLD_CONFIG_DIR/extensions" ] && [ "$(ls -A "$OLD_CONFIG_DIR/extensions" 2>/dev/null)" ]; then
    if [ ! "$(ls -A /var/lib/openclaw/extensions 2>/dev/null)" ]; then
        cp -a "$OLD_CONFIG_DIR/extensions"/* /var/lib/openclaw/extensions/ 2>/dev/null || true
        echo "Migrated extensions"
    fi
fi

# Migrate skills
if [ -d "$OLD_CONFIG_DIR/skills" ] && [ "$(ls -A "$OLD_CONFIG_DIR/skills" 2>/dev/null)" ]; then
    if [ ! "$(ls -A /var/lib/openclaw/skills 2>/dev/null)" ]; then
        cp -a "$OLD_CONFIG_DIR/skills"/* /var/lib/openclaw/skills/ 2>/dev/null || true
        echo "Migrated skills"
    fi
fi

# ── Step 4: Create system command symlink ──
echo "--- Step 4: Creating system commands ---"
# Find the actual openclaw binary
OPENCLAW_BIN=""
for candidate in \
    /usr/lib/openclaw/core/bin/openclaw \
    /usr/lib/openclaw/core/node_modules/.bin/openclaw \
    /usr/lib/openclaw/core/bin/cli.js; do
    if [ -f "$candidate" ]; then
        OPENCLAW_BIN="$candidate"
        break
    fi
done

if [ -n "$OPENCLAW_BIN" ]; then
    ln -sf "$OPENCLAW_BIN" /usr/bin/openclaw
    echo "Linked: /usr/bin/openclaw -> $OPENCLAW_BIN"
else
    echo "WARN: Could not find openclaw binary in slot-a, keeping existing /usr/bin/openclaw"
fi

# ── Step 5: Create openclaw system user ──
echo "--- Step 5: Setting up openclaw user ---"
if ! id openclaw &>/dev/null; then
    useradd -r -s /usr/sbin/nologin -d /var/lib/openclaw -c "OpenClaw AI Gateway" openclaw
    echo "Created user: openclaw"
else
    echo "User openclaw already exists"
fi

# Set ownership
chown -R openclaw:openclaw /var/lib/openclaw /var/log/openclaw /run/openclaw
chown -R root:openclaw /etc/openclaw
chmod 750 /etc/openclaw
chmod 755 /usr/lib/openclaw
# slot dirs readable by openclaw
chown -R root:openclaw /usr/lib/openclaw/slot-a /usr/lib/openclaw/slot-b 2>/dev/null || true

# ── Step 6: Stop old user-level service ──
echo "--- Step 6: Migrating service ---"
if systemctl --user is-active openclaw-gateway &>/dev/null 2>&1; then
    systemctl --user stop openclaw-gateway
    systemctl --user disable openclaw-gateway
    echo "Stopped user-level openclaw-gateway"
fi

# ── Step 7: Install system-level service ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/openclaw.service" ]; then
    cp "$SCRIPT_DIR/openclaw.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable openclaw
    echo "Installed system service: openclaw.service"
fi

# Install logrotate config
if [ -f "$SCRIPT_DIR/openclaw-logrotate.conf" ]; then
    cp "$SCRIPT_DIR/openclaw-logrotate.conf" /etc/logrotate.d/openclaw
    echo "Installed logrotate config"
fi

# ── Step 8: Record migration metadata ──
cat > /etc/openclaw/.migration <<EOF
migrated_at=$(date -Iseconds)
source=$CURRENT_OPENCLAW
active_slot=slot-a
old_config_dir=$OLD_CONFIG_DIR
EOF

echo ""
echo "=== Migration Complete ==="
echo ""
echo "System directories:"
echo "  Program:  /usr/lib/openclaw/core/ (-> slot-a)"
echo "  Config:   /etc/openclaw/"
echo "  Data:     /var/lib/openclaw/"
echo "  Logs:     /var/log/openclaw/"
echo "  Runtime:  /run/openclaw/"
echo ""
echo "Next steps:"
echo "  systemctl start openclaw     # Start system-level gateway"
echo "  systemctl status openclaw    # Check status"
echo "  curl http://127.0.0.1:18789/ # Verify dashboard"
echo ""
echo "Old config at $OLD_CONFIG_DIR is preserved (not deleted)."
