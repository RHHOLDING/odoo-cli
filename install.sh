#!/bin/bash

# Odoo CLI Installer
# Supports macOS and Linux
# Installs odoo-cli globally with XDG config discovery

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Odoo CLI Installer v1.6.0${NC}"
echo "==============================="
echo ""

# Check if running on supported OS
if [[ "$OSTYPE" != "darwin"* ]] && [[ "$OSTYPE" != "linux"* ]]; then
    echo -e "${RED}❌ This installer supports macOS and Linux only${NC}"
    exit 1
fi

# Detect OS for platform-specific settings
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    SHELL_RC="$HOME/.zshrc"
else
    OS_TYPE="linux"
    SHELL_RC="$HOME/.bashrc"
fi

echo -e "Detected OS: ${BLUE}$OS_TYPE${NC}"

# Check for Python 3.10+
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Python $PYTHON_VERSION found, but 3.10+ required${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        return 1
    fi
}

# Install Python via Homebrew if needed
install_python() {
    echo "Would you like to install Python 3.12 via Homebrew? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}❌ Homebrew not found. Please install from https://brew.sh${NC}"
            exit 1
        fi
        echo "Installing Python 3.12..."
        brew install python@3.12
        brew link python@3.12
    else
        echo -e "${RED}Installation cancelled${NC}"
        exit 1
    fi
}

# Main installation logic
main() {
    # 1. Check Python
    if ! check_python; then
        install_python
        if ! check_python; then
            echo -e "${RED}❌ Failed to install Python${NC}"
            exit 1
        fi
    fi

    # 2. Check for pipx (preferred) or pip
    if command -v pipx &> /dev/null; then
        echo -e "${GREEN}✓ Using pipx (recommended for CLI tools)${NC}"
        INSTALLER="pipx"
    else
        echo -e "${YELLOW}ℹ️  pipx not found, would you like to install it? (recommended) (y/n)${NC}"
        read -r response
        if [[ "$response" == "y" ]]; then
            echo "Installing pipx..."
            if command -v brew &> /dev/null; then
                brew install pipx
                pipx ensurepath
            else
                python3 -m pip install --user pipx
                python3 -m pipx ensurepath
            fi
            # Reload PATH
            export PATH="$HOME/.local/bin:$PATH"
            INSTALLER="pipx"
        else
            echo -e "${YELLOW}Using pip with user installation${NC}"
            INSTALLER="pip"
        fi
    fi

    # 3. Install odoo-cli
    echo ""
    echo "Installing odoo-cli..."

    REPO_PATH=$(dirname "$(realpath "$0")")

    if [ "$INSTALLER" == "pipx" ]; then
        # Uninstall if exists to ensure clean install
        pipx uninstall odoo-cli 2>/dev/null || true
        # Install from local path for development
        pipx install -e "$REPO_PATH"
    else
        # Use pip with user flag
        python3 -m pip install --user -e "$REPO_PATH"

        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            echo -e "${YELLOW}ℹ️  Added ~/.local/bin to PATH in $SHELL_RC${NC}"
            echo -e "${YELLOW}   Run 'source $SHELL_RC' to update current session${NC}"
        fi
    fi

    # 4. Create config directory (XDG standard)
    CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/odoo-cli"
    CONFIG_FILE="$CONFIG_DIR/.env"

    mkdir -p "$CONFIG_DIR"

    if [ ! -f "$CONFIG_FILE" ]; then
        echo ""
        echo "Creating sample configuration at $CONFIG_FILE"
        cat > "$CONFIG_FILE" << 'EOF'
# Odoo CLI Configuration
# This file is automatically discovered by odoo-cli
#
# Config Discovery Order:
# 1. ODOO_CONFIG environment variable (explicit path)
# 2. .env in current directory
# 3. .env in parent directories (up to 5 levels)
# 4. ~/.config/odoo-cli/.env (this file)
# 5. ~/.odoo-cli.env (legacy)

ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=admin@example.com
ODOO_PASSWORD=your-password

# Optional: JSON output by default (recommended for LLM automation)
# ODOO_CLI_JSON=1

# Optional settings
# ODOO_TIMEOUT=30
# ODOO_NO_VERIFY_SSL=false
EOF
        chmod 600 "$CONFIG_FILE"
        echo -e "${GREEN}✓ Sample config created at $CONFIG_FILE${NC}"
        echo -e "${YELLOW}  ⚠️  Update with your Odoo credentials${NC}"
    else
        echo -e "${GREEN}✓ Config already exists at $CONFIG_FILE${NC}"
    fi

    # 5. Verify installation
    echo ""
    echo "Verifying installation..."

    if command -v odoo-cli &> /dev/null; then
        echo -e "${GREEN}✅ Installation successful!${NC}"
        echo ""
        echo -e "${BLUE}Quick Start:${NC}"
        echo "  odoo-cli --help              # Show all commands"
        echo "  odoo-cli get-models          # Test connection"
        echo "  odoo-cli search res.partner '[]' --limit 5"
        echo ""
        echo -e "${BLUE}Configuration:${NC}"
        echo "  Global config: $CONFIG_FILE"
        echo "  Project config: .env in your project directory"
        echo "  Explicit path: export ODOO_CONFIG=/path/to/.env"
        echo ""
        echo -e "${BLUE}For LLM Agents:${NC}"
        echo "  odoo-cli works from any directory!"
        echo "  Config is discovered automatically."
        echo "  Use --json flag for structured output."
    else
        echo -e "${RED}❌ Installation may have succeeded but 'odoo-cli' command not found${NC}"
        echo "   You may need to:"
        echo "   1. Restart your terminal"
        echo "   2. Run: source $SHELL_RC"
        echo "   3. Check PATH includes ~/.local/bin"
    fi
}

# Run main installation
main

echo ""
echo -e "${BLUE}Need help?${NC} Check README or run: odoo-cli --help"
echo -e "${BLUE}Issues?${NC} https://github.com/RHHOLDING/odoo-cli/issues"