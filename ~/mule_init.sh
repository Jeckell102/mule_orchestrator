Bash
#!/bin/bash

# Define directories
ORCH_DIR=~/mule_orchestrator
WS_DIR=~/mule_ws
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "--- Starting Mule Global Sync: $TIMESTAMP ---"

# 1. Sync Orchestrator
if [ -d "$ORCH_DIR" ]; then
    echo "Processing Orchestrator..."
    cd $ORCH_DIR
    # Ensure build artifacts stay out
    git rm -r --cached build/ install/ log/ logs/ 2>/dev/null
    git add .
    git commit -m "Session Sync: $TIMESTAMP" --allow-empty
    git push origin main
else
    echo "Warning: $ORCH_DIR not found."
fi

# 2. Sync Workspace
if [ -d "$WS_DIR" ]; then
    echo "Processing Workspace..."
    cd $WS_DIR
    git add .
    git commit -m "Session Sync: $TIMESTAMP" --allow-empty
    git push origin main
else
    echo "Warning: $WS_DIR not found."
fi

echo "--- Sync Complete ---"