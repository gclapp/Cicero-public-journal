#!/bin/bash
# ClawMetry launcher with proper gateway token
export OPENCLAW_HOME=/home/ubuntu/.openclaw
export OPENCLAW_GATEWAY_URL=http://localhost:23675
export OPENCLAW_GATEWAY_TOKEN=84718ffbbc4e1f56a34010b74d1d3b529622efb98929df3a
export CLAWMETRY_FLEET_KEY=public-access
/usr/local/bin/clawmetry --host 0.0.0.0 --port 8900 --no-debug "$@"
