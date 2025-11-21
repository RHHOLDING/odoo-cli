# Installation Guide for macOS

## Quick Install (Recommended)

```bash
# Clone and install with one command
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli
./install.sh
```

The installer will:
- ✅ Check for Python 3.10+ (installs via Homebrew if needed)
- ✅ Install pipx if not present (best practice for CLI tools)
- ✅ Install the odoo CLI globally
- ✅ Create sample configuration file
- ✅ Set proper permissions

## Manual Installation Options

### Option 1: Using pipx (Recommended)
```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install odoo-cli
pipx install git+https://github.com/RHHOLDING/odoo-cli.git

# For development (editable install)
pipx install -e /path/to/odoo-xml-cli
```

### Option 2: Using Homebrew Python
```bash
# Install Python 3.12
brew install python@3.12

# Install globally with pip
pip3.12 install git+https://github.com/RHHOLDING/odoo-cli.git
```

### Option 3: Using Virtual Environment
```bash
# Create virtual environment
python3 -m venv ~/odoo-cli-env
source ~/odoo-cli-env/bin/activate

# Install
pip install git+https://github.com/RHHOLDING/odoo-cli.git

# Create alias for easy access
echo 'alias odoo="~/odoo-cli-env/bin/odoo"' >> ~/.zshrc
source ~/.zshrc
```

## Configuration

### 1. Environment Variables (for LLMs/CI)
```bash
export ODOO_URL=https://your-instance.odoo.com
export ODOO_DB=your-database
export ODOO_USERNAME=admin@example.com
export ODOO_PASSWORD=your-password
```

### 2. Configuration File (for Humans)
```bash
# Create .env in your project directory
cat > .env << EOF
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=admin@example.com
ODOO_PASSWORD=your-password
EOF

# Set secure permissions
chmod 600 .env
```

## Verify Installation

```bash
# Check if installed
odoo --help

# Test connection
odoo get-models

# Start interactive shell
odoo shell
```

## Troubleshooting

### Command not found
```bash
# If using pipx
pipx ensurepath
source ~/.zshrc

# If using pip
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### Python version issues
```bash
# Install Python 3.12 with Homebrew
brew install python@3.12
brew link python@3.12

# Or use pyenv for version management
brew install pyenv
pyenv install 3.12.0
pyenv global 3.12.0
```

### SSL Certificate errors
```bash
# For self-signed certificates
odoo get-models --no-verify-ssl

# Or install certificates
brew install ca-certificates
```

## Uninstall

```bash
# Use the uninstall script
./uninstall.sh

# Or manually with pipx
pipx uninstall odoo-xml-cli

# Or manually with pip
pip uninstall odoo-xml-cli
```

## System Requirements

- **macOS**: 11.0 (Big Sur) or later
- **Python**: 3.10 or later
- **Memory**: 100MB free RAM
- **Disk**: 50MB free space
- **Network**: Internet connection for Odoo access

## Security Notes

⚠️ **Important**: Never commit `.env` files to git!

Add to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

For production use:
- Use environment variables instead of .env files
- Store credentials in macOS Keychain (future feature)
- Use read-only Odoo users when possible
- Enable 2FA on your Odoo account

## Next Steps

1. Configure your Odoo connection
2. Test with `odoo get-models`
3. Explore commands with `odoo --help`
4. Use `odoo shell` for interactive exploration

## Support

- **Issues**: https://github.com/RHHOLDING/odoo-cli/issues
- **Documentation**: See README.md
- **Examples**: Run `odoo --help` for each command