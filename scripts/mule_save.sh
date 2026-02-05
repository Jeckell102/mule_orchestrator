#!/bin/bash

# --- AEGIS GARDENER ENVIRONMENT INITIALIZER ---
echo "⚙️  Initializing MuleLab Environment..."

# 1. Install Dependencies
pip install -U google-generativeai psutil pandas

# 2. Set API Key (Update this with your actual key)
export GOOGLE_API_KEY="AIzaSyBGtzSb4cj3qeprztu6BRWYtTT677NLRng"

# 3. Verify Python Version (Must be 3.10+)
PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Python Version: $PYTHON_VER"

# 4. Check Database Integrity
if [ -f "logs/mule_results.db" ]; then
    echo "📂 Database: Found"
else
    echo "⚠️  Database: Missing (Will be created on first run)"
fi

# 5. Export for VS Code session
echo "✅ Environment Ready."
echo "👉 RUN THIS TO ACTIVATE: source mule_init.sh"