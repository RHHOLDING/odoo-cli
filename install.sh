#!/bin/bash

# Odoo XML-CLI Installer for macOS
# Optimized for Mac users who prefer simple installation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Odoo XML-CLI Installer for macOS"
echo "===================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This installer is designed for macOS only${NC}"
    exit 1
fi

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

    # 3. Install odoo-xml-cli
    echo ""
    echo "Installing odoo-xml-cli..."

    REPO_PATH=$(dirname "$(realpath "$0")")

    if [ "$INSTALLER" == "pipx" ]; then
        # Uninstall if exists to ensure clean install
        pipx uninstall odoo-xml-cli 2>/dev/null || true
        # Install from local path for development
        pipx install -e "$REPO_PATH"
    else
        # Use pip with user flag
        python3 -m pip install --user -e "$REPO_PATH"

        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
            echo -e "${YELLOW}ℹ️  Added ~/.local/bin to PATH in ~/.zshrc${NC}"
            echo -e "${YELLOW}   Run 'source ~/.zshrc' to update current session${NC}"
        fi
    fi

    # 4. Create sample .env file if not exists
    if [ ! -f "$HOME/.odoo_cli.env" ]; then
        echo ""
        echo "Creating sample configuration at ~/.odoo_cli.env"
        cat > "$HOME/.odoo_cli.env" << 'EOF'
# Odoo CLI Configuration
# Copy this file to your project directory as .env
# Or set these as environment variables

ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=admin@example.com
ODOO_PASSWORD=your-password

# Optional settings
# ODOO_TIMEOUT=30
# ODOO_NO_VERIFY_SSL=false
EOF
        chmod 600 "$HOME/.odoo_cli.env"
        echo -e "${GREEN}✓ Sample config created at ~/.odoo_cli.env${NC}"
        echo -e "${YELLOW}  ⚠️  Remember to update it with your Odoo credentials${NC}"
    fi

    # 5. Verify installation
    echo ""
    echo "Verifying installation..."

    if command -v odoo &> /dev/null; then
        echo -e "${GREEN}✅ Installation successful!${NC}"
        echo ""
        echo "You can now use the odoo command:"
        echo "  odoo --help              # Show all commands"
        echo "  odoo get-models          # Test connection"
        echo "  odoo shell               # Interactive shell"
        echo ""
        echo "Configuration:"
        echo "  1. Copy ~/.odoo_cli.env to your project as .env"
        echo "  2. Update with your Odoo credentials"
        echo "  3. Set chmod 600 .env for security"
        echo ""
        echo "Or set environment variables:"
        echo "  export ODOO_URL=https://your-instance.odoo.com"
        echo "  export ODOO_DB=your-database"
        echo "  export ODOO_USERNAME=admin@example.com"
        echo "  export ODOO_PASSWORD=your-password"
    else
        echo -e "${RED}❌ Installation may have succeeded but 'odoo' command not found${NC}"
        echo "   You may need to:"
        echo "   1. Restart your terminal"
        echo "   2. Run: source ~/.zshrc"
        echo "   3. Check PATH includes ~/.local/bin"
    fi
}

# Run main installation
main

echo ""
echo "Need help? Check the README or run: odoo --help"