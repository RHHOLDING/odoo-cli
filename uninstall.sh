#!/bin/bash

# Odoo XML-CLI Uninstaller for macOS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🗑️  Odoo XML-CLI Uninstaller"
echo "============================"
echo ""

# Check for pipx installation
if command -v pipx &> /dev/null && pipx list | grep -q "odoo-xml-cli"; then
    echo "Removing odoo-xml-cli installed via pipx..."
    pipx uninstall odoo-xml-cli
    echo -e "${GREEN}✓ Removed pipx installation${NC}"
fi

# Check for pip installation
if pip3 list | grep -q "odoo-xml-cli"; then
    echo "Removing odoo-xml-cli installed via pip..."
    pip3 uninstall -y odoo-xml-cli
    echo -e "${GREEN}✓ Removed pip installation${NC}"
fi

# Ask about config files
echo ""
echo -e "${YELLOW}Remove configuration file ~/.odoo_cli.env? (y/n)${NC}"
read -r response
if [[ "$response" == "y" ]]; then
    rm -f "$HOME/.odoo_cli.env"
    echo -e "${GREEN}✓ Configuration file removed${NC}"
else
    echo "Configuration file kept at ~/.odoo_cli.env"
fi

# Ask about shell history
if [ -f "$HOME/.odoo_cli_history" ]; then
    echo ""
    echo -e "${YELLOW}Remove shell history ~/.odoo_cli_history? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        rm -f "$HOME/.odoo_cli_history"
        echo -e "${GREEN}✓ Shell history removed${NC}"
    else
        echo "Shell history kept at ~/.odoo_cli_history"
    fi
fi

echo ""
echo -e "${GREEN}✅ Uninstallation complete!${NC}"