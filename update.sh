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
echo "🎉 v1.5.1 - Flexible Context File Paths"
echo "   Context files can now be stored ANYWHERE!"
echo
echo "   3 Ways to access context files:"
echo "   1. --context-file flag (explicit):"
echo "      odoo-cli context show --context-file /path/to/.odoo-context.json"
echo
echo "   2. ODOO_CONTEXT_FILE env var (recommended):"
echo "      export ODOO_CONTEXT_FILE=/path/to/.odoo-context.json"
echo "      odoo-cli context show  # Works from any directory!"
echo
echo "   3. Parent directory search (auto-discovery):"
echo "      Just run from any subdirectory, it finds the file!"
echo
echo "📖 Setup example:"
echo "   export ODOO_CONTEXT_FILE=/Users/andre/Documents/dev/ODOO-MAIN/.odoo-context.json"
echo "   odoo-cli context show         # Display business metadata"
echo "   odoo-cli context guide --task create-sales-order"
echo "   odoo-cli context validate --strict"
echo
echo "📝 To enable JSON output by default:"
echo "   export ODOO_CLI_JSON=1"
echo
echo "   Or add to your ~/.zshrc or ~/.bashrc:"
echo "   echo 'export ODOO_CLI_JSON=1' >> ~/.zshrc"
