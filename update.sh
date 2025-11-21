#!/bin/bash
# Quick update script for odoo-cli
# Updates from git and reinstalls with pipx

set -e  # Exit on error

echo "🔄 Updating odoo-cli..."
echo

# Step 1: Git pull latest changes
echo "📥 Pulling latest changes from git..."
git pull origin main

# Step 2: Reinstall with pipx
echo
echo "📦 Reinstalling odoo-cli with pipx..."
pipx install --force .

# Step 3: Show version
echo
echo "✅ Update complete!"
odoo-cli --version

echo
echo "📝 To enable JSON output by default:"
echo "   export ODOO_CLI_JSON=1"
echo
echo "   Or add to your ~/.zshrc or ~/.bashrc:"
echo "   echo 'export ODOO_CLI_JSON=1' >> ~/.zshrc"
