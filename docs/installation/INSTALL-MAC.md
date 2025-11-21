# Installation Guide for macOS
**Quick Setup for Odoo JSON-RPC CLI on Mac**

---

## Prerequisites

- **macOS 10.13+** (any recent version)
- **Python 3.10+** (check: `python3 --version`)
- **Git** (check: `git --version`)
- **Odoo credentials** (URL, Database, Username, Password)

---

## Step 1: Install Python (if needed)

### Option A: Using Homebrew (Recommended)
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Verify installation
python3 --version  # Should show 3.10+
```

### Option B: Using MacPorts
```bash
sudo port install python310
sudo port select --set python3 python310
```

### Option C: Using conda
```bash
conda create -n odoo-cli python=3.10
conda activate odoo-cli
```

---

## Step 2: Clone or Get the Repository

### Option A: Clone from GitHub
```bash
# Clone the repository
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli

# Switch to development branch (if needed)
git checkout 002-jsonrpc-migration
```

### Option B: Use Existing Local Copy
```bash
cd /Users/andre/Documents/dev/ODOO-MAIN/odoo-xml-cli
```

---

## Step 3: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Verify Python path
which python3  # Should show .../venv/bin/python3
```

---

## Step 4: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install package in development mode
pip install -e .

# Verify installation
odoo --version  # Or: odoo get-models (to test)
```

---

## Step 5: Configure Credentials

### Option A: Using .env File (Recommended for Development)
```bash
# Create .env file in project root
cat > .env << 'EOF'
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-email@example.com
ODOO_PASSWORD=your-password
ODOO_TIMEOUT=30
EOF

# Secure file permissions
chmod 600 .env

# Add to .gitignore (never commit!)
echo ".env" >> .gitignore
```

### Option B: Using Environment Variables
```bash
# Add to ~/.zprofile or ~/.bash_profile
export ODOO_URL=https://your-instance.odoo.com
export ODOO_DB=your-database
export ODOO_USERNAME=your-email@example.com
export ODOO_PASSWORD=your-password

# Reload shell
source ~/.zprofile  # or source ~/.bash_profile
```

### Option C: Using ~/.odoo-cli/config (For System-Wide Installation)
```bash
# Create config directory
mkdir -p ~/.odoo-cli

# Create config file
cat > ~/.odoo-cli/config << 'EOF'
[odoo]
url = https://your-instance.odoo.com
database = your-database
username = your-email@example.com
password = your-password
timeout = 30
EOF

# Secure it
chmod 600 ~/.odoo-cli/config
```

---

## Step 6: Test Installation

```bash
# Test 1: Basic connectivity
odoo get-models

# Test 2: Search for records
odoo search res.partner '[]' --limit 5

# Test 3: Get field definitions
odoo get-fields res.partner

# If all work: ✅ Installation complete!
```

---

## Troubleshooting

### Error: "command not found: odoo"

**Solution 1:** Make sure virtual environment is activated
```bash
source venv/bin/activate
```

**Solution 2:** Reinstall the package
```bash
pip install -e .
```

**Solution 3:** Use full path
```bash
python3 -m odoo_cli.cli get-models
```

### Error: "Python 3.10+ required"

**Solution:** Check Python version and upgrade if needed
```bash
python3 --version

# If < 3.10, upgrade via Homebrew
brew install python@3.10
alias python3=/usr/local/bin/python3.10
```

### Error: "Connection refused" or "Authentication failed"

**Solution:** Check credentials
```bash
# Verify .env file
cat .env

# Test manually
odoo --url https://test.odoo.com \
     --db test_db \
     --username admin \
     get-models
```

### Error: "Module requests not found"

**Solution:** Install dependencies
```bash
# Deactivate and reactivate venv
deactivate
source venv/bin/activate

# Reinstall
pip install -e .
```

---

## Uninstalling

```bash
# If using virtual environment (recommended)
deactivate
rm -rf venv/

# If installed system-wide
pip uninstall odoo-xml-cli
```

---

## Using the CLI

### Quick Start Commands

```bash
# List all models
odoo get-models

# Search partners
odoo search res.partner '[["is_company", "=", true]]' --limit 10

# Get field definitions
odoo get-fields sale.order

# Execute custom method
odoo execute res.partner search_count --args '[[]]'

# Interactive shell
odoo shell
```

### For Large Aggregations

```bash
# Use Python script template from docs/guides/LLM-DEVELOPMENT.md
python3 docs/examples/aggregation_script.py
```

---

## Next Steps

1. **Read:** [docs/README.md](../README.md) - Main documentation hub
2. **Learn:** [docs/guides/LLM-DEVELOPMENT.md](../guides/LLM-DEVELOPMENT.md) - LLM usage guide
3. **Debug:** [docs/ERROR-HANDLING.md](../ERROR-HANDLING.md) - Error troubleshooting
4. **Examples:** [docs/examples/](../examples/) - Real code examples

---

## System Requirements Summary

| Component | Requirement | Check |
|-----------|-------------|-------|
| OS | macOS 10.13+ | `sw_vers` |
| Python | 3.10+ | `python3 --version` |
| pip | Latest | `pip --version` |
| git | Latest | `git --version` |
| Network | Internet access | `ping google.com` |

---

## Support

If you encounter issues:

1. Check the [ERROR-HANDLING.md](../ERROR-HANDLING.md) guide
2. Review your credentials in `.env`
3. Test Odoo connectivity: `curl https://your-url.odoo.com`
4. Check logs: `ODOO_DEBUG=1 odoo get-models`

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Status:** Production Ready ✅
