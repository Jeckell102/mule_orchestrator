#!/bin/bash
# setup_mule.sh - Automated Environment & Git Prep

echo "🚀 Starting MuleLab Automation Setup..."

# 1. Install/Update Dependencies
# GitPython is used for the automated push feature
echo "🛠️  Step 1: Installing dependencies (GenAI, Weather, Git)..."
pip3 install -U google-genai requests GitPython --quiet

# 2. Folder structure check
echo "📂 Step 2: Verifying directory structure..."
mkdir -p ~/mule_orchestrator/prompts

# 3. Alias automation
if ! grep -q "alias mule=" ~/.bashrc; then
    echo "🔗 Step 3: Adding 'mule' alias to ~/.bashrc..."
    echo "alias mule='python3 ~/mule_orchestrator/mule_orchestrator.py'" >> ~/.bashrc
else
    echo "✅ Step 3: Alias already exists."
fi

echo "---"
echo "✅ Setup Complete. Run 'source ~/.bashrc' and then 'mule'."