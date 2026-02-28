#!/bin/bash
# Healthcheck Security Hardening Script
# Generated: 2026-02-28
# Run with explicit approvals only

set -e

echo "=== OpenClaw Security Hardening ==="
echo "Date: $(date)"
echo ""

# Step 1: Enable UFW Firewall
echo "Step 1: Enabling UFW Firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 3000/tcp comment 'Node.js service'
sudo ufw allow 8900/tcp comment 'ClawMetry'
sudo ufw --force enable
echo "✅ Firewall enabled"
echo ""

# Step 2: Check SSH configuration
echo "Step 2: Checking SSH configuration..."
echo "Current SSH settings:"
grep -E "^(Port|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication)" /etc/ssh/sshd_config 2>/dev/null || echo "Could not read SSH config"
echo ""

# Step 3: Fix OpenClaw gateway token
echo "Step 3: Checking OpenClaw gateway tokens..."
openclaw config get gateway.auth.token
openclaw config get gateway.remote.token
echo ""

echo "=== Hardening complete ==="
