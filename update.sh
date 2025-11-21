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
echo "🎉 v1.5.0 - New Feature: Business Context for LLM Agents"
echo "   - odoo-cli context show         # Display business metadata"
echo "   - odoo-cli context guide --task # Task-specific guidance"
echo "   - odoo-cli context validate     # Validate context files"
echo
echo "📖 Setup context for your project:"
echo "   cp .odoo-context.json5.example .odoo-context.json"
echo "   # Edit with your business metadata"
echo "   odoo-cli context validate --strict"
echo
echo "📝 To enable JSON output by default:"
echo "   export ODOO_CLI_JSON=1"
echo
echo "   Or add to your ~/.zshrc or ~/.bashrc:"
echo "   echo 'export ODOO_CLI_JSON=1' >> ~/.zshrc"
